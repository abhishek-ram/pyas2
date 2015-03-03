from django.core.management.base import BaseCommand, CommandError
from pyas2 import models

class Command(BaseCommand):
    help = 'Deamon that watches for files in all outboxes'

    def handle(self, *args, **options):
	cond = threading.Condition()
	tasks = set()   
	dir_watch_data = []
	orgs = models.Organizations.objects.all()
	partners = models.Partners.objects.all()
	for partner in partners:
	    for org in orgs:
		dir_watch_data.append(partner+'/outbox/'+org)
	if not dir_watch_data:
	    logger.error(u'Nothing to watch!')
	    sys.exit(0)
	if os.name == 'nt':
	    #for windows: start a thread per directory watcher
	    for dir_watch in dir_watch_data:
		dir_watch_thread = threading.Thread(target=windows_event_handler, args=(logger,dir_watch,cond,tasks))
            	dir_watch_thread.daemon = True  #do not wait for thread when exiting
            	dir_watch_thread.start()
	else:
            #for linux: one watch-thread, but multiple watches. 
            dir_watch_thread = threading.Thread(target=linux_event_handler, args=(logger,dir_watch_data,cond,tasks))
            dir_watch_thread.daemon = True  #do not wait for thread when exiting
            dir_watch_thread.start()
	active_receiving = False
	timeout = 2.0
	cond.acquire()
	while True:
	    cond.wait(timeout=timeout)    #get back when results, or after timeout sec
	    if tasks:
		if not active_receiving:    #first request (after tasks have been  fired, or startup of dirmonitor)
		    active_receiving = True
                    last_time = time.time()
		else:     #active receiving events
		    current_time = time.time()
		    if current_time - last_time >= timeout:
		    	continue
	#self.stdout.write('Successfully finished send all command')
