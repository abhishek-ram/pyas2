from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from pyas2 import models
from pyas2 import pyas2init
from pyas2 import as2utils
import time
import atexit
import socket
import os
import sys
import subprocess
import threading

if os.name == 'nt':
    try:
        import win32file
        import win32con
    except Exception as msg:
        raise ImportError(u'Dependency failure: pyas2 directory monitoring requires '
                          u'python library "Python Win32 Extensions" on windows.')


    def windows_event_handler(logger, dir_watch, cond, tasks):
        ACTIONS = {
            1: "Created  ",  # test for printing results
            2: "Deleted  ",
            3: "Updated  ",
            4: "Rename from",
            5: "Rename to",
        }
        FILE_LIST_DIRECTORY = 0x0001
        hDir = win32file.CreateFile(dir_watch['path'],  # to directory
                                    FILE_LIST_DIRECTORY,  # access (read/write) mode
                                    # share mode: FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE
                                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                                    None,  # security descriptor
                                    win32con.OPEN_EXISTING,  # how to create
                                    # file attributes: FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED
                                    win32con.FILE_FLAG_BACKUP_SEMANTICS,
                                    None,
                                    )
        # detecting right events is not easy in windows :-(
        # want to detect: new file,  move, drop, rename, write/append to file
        # only FILE_NOTIFY_CHANGE_LAST_WRITE: copy yes, no move
        # for rec=True: event that subdirectory itself is updated (for file deletes in dir)
        while True:
            results = win32file.ReadDirectoryChangesW(hDir,
                                                      8192,  # buffer size was 1024, do not want to miss anything
                                                      False,  # recursive
                                                      win32con.FILE_NOTIFY_CHANGE_FILE_NAME |
                                                      # ~ win32con.FILE_NOTIFY_CHANGE_DIR_NAME |
                                                      # ~ win32con.FILE_NOTIFY_CHANGE_ATTRIBUTES |
                                                      # ~ win32con.FILE_NOTIFY_CHANGE_SIZE |
                                                      # ~ win32con.FILE_NOTIFY_CHANGE_SECURITY |
                                                      # ~ win32con.FILE_NOTIFY_CHANGE_CREATION |
                                                      # ~ win32con.FILE_NOTIFsY_CHANGE_LAST_ACCESS |
                                                      win32con.FILE_NOTIFY_CHANGE_LAST_WRITE,
                                                      None,
                                                      None
                                                      )
            if results:
                # for each incoming event: place route to run in a set. Main thread takes action.
                for action, filename in results:
                    pyas2init.logger.debug(u'Event: %(action)s %(filename)s',
                                           {'action': ACTIONS.get(action, "Unknown"), 'filename': filename})
                for action, filename in results:
                    if action in [1, 3, 5]:  # and fnmatch.fnmatch(filename, dir_watch['filemask']):
                        # ~ if dir_watch['rec'] and os.sep in filename:
                        # ~ continue
                        full_filename = os.path.join(dir_watch['path'], filename)
                        if os.path.isfile(full_filename):
                            cond.acquire()
                            tasks.add((dir_watch['organization'], dir_watch['partner'], full_filename))
                            cond.notify()
                            cond.release()
                            # break       #the route is triggered, do not need to trigger more often
                            # end of windows-specific ##############################################
else:
    # linux specific ###########################################################################################
    try:
        import pyinotify
    except Exception as msg:
        raise ImportError(
            u'Dependency failure: bots directory monitoring requires python library "pyinotify" on linux.')


    class LinuxEventHandler(pyinotify.ProcessEvent):
        """
        incoming event contains:
            dir=<bool>    check? - looks like the mask does never contains dirs.
            mask=0x80
            maskname=eg IN_MOVED_TO
            name=<filename>
            path=<path>
            pathname=<path>/<filename>
            wd=<int>     #the watch
        """

        def my_init(self, logger, dir_watch_data, cond, tasks):
            self.dir_watch_data = dir_watch_data
            self.cond = cond
            self.tasks = tasks
            self.logger = logger

        def process_IN_CREATE(self, event):
            """ these events are not needed, but otherwise auto_add does not work...."""
            pass

        def process_default(self, event):
            """ for each incoming event: place route to run in a set. Main thread sends actual job.
            """
            # ~ if event.mask == pyinotify.IN_CLOSE_WRITE and event.dir and self.watch_data[event.wd][2]:
            # ~ logger.info(u'new directory!!"%s %s".',event.)
            # ~ print 'event detected',event.name,event.maskname, event.wd
            if not event.dir:
                for dir_watch in self.dir_watch_data:
                    if event.pathname.startswith(dir_watch['path']):
                        # if fnmatch.fnmatch(event.name, dir_watch['filemask']):
                        self.cond.acquire()
                        self.tasks.add((dir_watch['organization'], dir_watch['partner'], event.pathname))
                        self.cond.notify()
                        self.cond.release()


    def linux_event_handler(logger, dir_watch_data, cond, tasks):
        watch_manager = pyinotify.WatchManager()
        mask = pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MODIFY | pyinotify.IN_CREATE
        for dir_watch in dir_watch_data:
            logger.info(_(u'Watching directory %s' % dir_watch['path']))
            watch_manager.add_watch(path=dir_watch['path'], mask=mask, rec=False, auto_add=True, do_glob=True)
        handler = LinuxEventHandler(logger=logger, dir_watch_data=dir_watch_data, cond=cond, tasks=tasks)
        notifier = pyinotify.Notifier(watch_manager, handler)
        notifier.loop()
        # end of linux-specific ##################################################################################


class Command(BaseCommand):
    help = _(u'Daemon process that watches the outbox of all as2 partners and '
             u'triggers sendmessage when files become available')

    def handle(self, *args, **options):
        pyas2init.logger.info(_(u'Starting PYAS2 send daemon.'))
        try:
            engine_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            engine_socket.bind(('127.0.0.1', pyas2init.gsettings['daemon_port']))
        except socket.error:
            engine_socket.close()
            raise CommandError(_(u'An instance of the send daemon is already running'))
        else:
            atexit.register(engine_socket.close)
        cond = threading.Condition()
        tasks = set()
        dir_watch_data = []
        orgs = models.Organization.objects.all()
        partners = models.Partner.objects.all()
        python_executable_path = pyas2init.gsettings['python_path']
        managepy_path = pyas2init.gsettings['managepy_path']
        for partner in partners:
            for org in orgs:
                dir_watch_data.append({})
                dir_watch_data[-1]['path'] = as2utils.join(pyas2init.gsettings['root_dir'], 'messages',
                                                           partner.as2_name, 'outbox', org.as2_name)
                dir_watch_data[-1]['organization'] = org.as2_name
                dir_watch_data[-1]['partner'] = partner.as2_name
        if not dir_watch_data:
            pyas2init.logger.error(_(u'No partners have been configured!'))
            sys.exit(0)
        pyas2init.logger.info(_(u'Process existing files in the directory.'))
        for dir_watch in dir_watch_data:
            files = [f for f in os.listdir(dir_watch['path']) if os.path.isfile(as2utils.join(dir_watch['path'], f))]
            for file in files:
                lijst = [python_executable_path, managepy_path, 'sendas2message', '--delete', dir_watch['organization'],
                         dir_watch['partner'], as2utils.join(dir_watch['path'], file)]
                pyas2init.logger.info(u'Send as2 message with params "%(task)s".', {'task': lijst})
                subprocess.Popen(lijst)
        if os.name == 'nt':
            # for windows: start a thread per directory watcher
            for dir_watch in dir_watch_data:
                dir_watch_thread = threading.Thread(target=windows_event_handler,
                                                    args=(pyas2init.logger, dir_watch, cond, tasks))
                dir_watch_thread.daemon = True  # do not wait for thread when exiting
                dir_watch_thread.start()
        else:
            # for linux: one watch-thread, but multiple watches.
            dir_watch_thread = threading.Thread(target=linux_event_handler,
                                                args=(pyas2init.logger, dir_watch_data, cond, tasks))
            dir_watch_thread.daemon = True  # do not wait for thread when exiting
            dir_watch_thread.start()
        # this main thread get the results from the watch-thread(s).
        pyas2init.logger.info(_(u'PYAS2 send daemon started started.'))
        active_receiving = False
        timeout = 2.0
        cond.acquire()
        while True:
            # this functions as a buffer: all events go into set tasks.
            # the tasks are fired to jobqueue after TIMOUT sec.
            # this is to avoid firing to many tasks to jobqueue; events typically come in bursts.
            # is value of timeout is larger, reaction times are slower...but less tasks are fired to jobqueue.
            # in itself this is not a problem, as jobqueue will alos discard duplicate jobs.
            # 2 sec seems to e a good value: reasonable quick, not to nervous.
            cond.wait(timeout=timeout)  # get back when results, or after timeout sec
            if tasks:
                if not active_receiving:  # first request (after tasks have been  fired, or startup of dirmonitor)
                    active_receiving = True
                    last_time = time.time()
                else:  # active receiving events
                    current_time = time.time()
                    if current_time - last_time >= timeout:
                        try:
                            for task in tasks:
                                lijst = [python_executable_path, managepy_path, 'sendas2message', '--delete', task[0],
                                         task[1], task[2]]
                                pyas2init.logger.info(u'Send as2 message with params "%(task)s".', {'task': lijst})
                                subprocess.Popen(lijst)
                        except Exception as msg:
                            pyas2init.logger.info(u'Error in running task: "%(msg)s".', {'msg': msg})
                        tasks.clear()
                        active_receiving = False
                    else:
                        pyas2init.logger.debug(u'time difference to small.')
                        last_time = current_time
        cond.release()
        sys.exit(0)

    # self.stdout.write('Successfully finished send all command')
