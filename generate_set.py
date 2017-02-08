import os, sys
import config

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE","tigaserver_project.settings")
sys.path.append(proj_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

from tigaserver_app.models import Report,Photo
from json import dumps
import datetime
import json

#oldest_report_blocked_in_filter = "2016-01-13 02:10:12.827+01"
id_reports_unclassified_adults_2014 = config.params['ids']

reports_unclassified_adults_2014 = Report.objects.filter(version_UUID__in=id_reports_unclassified_adults_2014).exclude(hide=True)
reports_breeding_sites_2014 = Report.objects.filter(creation_time__year=2014).filter(type='site').exclude(note__icontains='#345').exclude(photos=None).exclude(hide=True)
reports_passed_coarse_filter = Report.objects.filter(creation_time__gte=datetime.date(2016,01,13)).exclude(note__icontains='#345').exclude(photos=None).exclude(hide=True)

all_reports = reports_unclassified_adults_2014 | reports_breeding_sites_2014 | reports_passed_coarse_filter
reports_filtered = filter(lambda x: not x.deleted and x.latest_version, all_reports)

print len(reports_filtered)
data = []

for report in reports_filtered:
	the_photos = Photo.objects.filter(report__version_UUID=report.version_UUID)
	for photo in the_photos:
		if photo.hide is False:
			data.append({'uuid':photo.uuid,'id':photo.id,'location':{'lat':report.lat,'lng':report.lon},'creation_time': str(report.creation_time),'report_id':report.version_UUID})

with open('outfile.json','w') as outfile:
	json.dump(data,outfile,indent=2)