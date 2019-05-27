import datetime
import json
import requests
import time
import os, sys
from django.core.wsgi import get_wsgi_application
import config
import datetime as DT

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path)
application = get_wsgi_application()

from tigaserver_app.models import Report, Photo

API_KEY = config.params['API_KEY']
BASE_URL = config.params['BASE_URL']
TASK_ENDPOINT = config.params['TASK_ENDPOINT']
PROJECT_ID = config.params['PROJECT_ID']
RECORD_LIMIT = config.params['RECORD_LIMIT']

counter = 0
endloop = False

'''
if config.params['PROJECT_ID'] == 1:
    k_input = input("Work will be executed against PRODUCTION project. Are you ABSOLUTELY SURE YOU WANT TO PROCEED? (Y/N)")
    if k_input != 'Y':
        sys.exit()
'''

def nap(nap_interval,total_time):
    nap_time = nap_interval
    remaining_nap_time = total_time
    endnap = False
    while not (endnap):
        print("Sleeping... " + str(remaining_nap_time))
        time.sleep(nap_time)
        remaining_nap_time = remaining_nap_time - nap_time
        if remaining_nap_time == 0:
            endnap = True

reports_in_pybossa = []
pictures_in_pybossa = []

while not (endloop):
    offset = counter * RECORD_LIMIT
    res = requests.get(BASE_URL + TASK_ENDPOINT + '?offset=' + str(offset) + "&project_id=" + str(PROJECT_ID))
    print "Obtaining tasks up to " + str(offset) + " records"
    if res.status_code == 200:
        print "Records up to " + str(offset) + " obtained succesfully"
        if int(res.headers['X-RateLimit-Remaining']) < 10:
            nap(10,300)
        else:
            counter = counter + 1
            data = json.loads(res.content)
            if (len(data) == 0):
                endloop = True
            else:
                for bit in data:
                    print bit['info']['uuid']
                    reports_in_pybossa.append(bit['info']['report_id'])
                    pictures_in_pybossa.append(bit['info']['uuid'])
    else:
        print "Failed to obtain records up to " + str(offset)

reports_in_tigaserver = []
#this is an additional precaution. Make sure that all reports have been seen by someone in the coarse filter (most recent report
#in list is at least three days old)
today = DT.date.today()
three_days_ago = today - DT.timedelta(days=3)

reports_passed_coarse_filter = Report.objects.filter(creation_time__gte=datetime.date(2016, 01, 13)).filter(creation_time__lt=three_days_ago).exclude(note__icontains='#345').exclude(photos=None).exclude(type='site').exclude(hide=True)
all_reports = reports_passed_coarse_filter.exclude(version_UUID__in=reports_in_pybossa)
reports_filtered = filter(lambda x: not x.deleted and x.latest_version, all_reports)

if len(reports_filtered) == 0:
    print "No pictures to upload, all done!"
    sys.exit()

added_pictures = 0

for report in reports_filtered:
    the_photos = Photo.objects.filter(report__version_UUID=report.version_UUID)
    for photo in the_photos:
        if photo.hide is False and photo.uuid not in pictures_in_pybossa:
            location = dict(lat=report.lat,lng=report.lon)
            info = dict(id=photo.id,uuid=photo.uuid,creation_time=str(report.creation_time),report_id=report.version_UUID,location=location)
            data = dict(info=info, project_id=PROJECT_ID,n_answers=5)
            data = json.dumps(data)
            headers = {'Content-Type': 'application/json'}
            print "Uploading task for picture - " + photo.uuid + " ,report - " + report.version_UUID
            res = requests.post(BASE_URL + TASK_ENDPOINT + '?api_key=' + API_KEY, data=data, headers=headers)
            if res.status_code == 200:
                added_pictures = added_pictures + 1
                print "Upload successful!"
                if int(res.headers['X-RateLimit-Remaining']) < 10:
                    nap(10, 300)
                else:
                    pass
            else:
                print "Upload failed!"

if added_pictures == 0 and len(reports_filtered) > 0:
    print "No pictures uploaded, probably everything is up to date. All done!"