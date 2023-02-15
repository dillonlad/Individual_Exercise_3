"""Hello Analytics Reporting API V4."""
from operator import itemgetter
import os
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']

KEY_FILE_LOCATION = 'app/inwaitoftomorrow-1f1619d16199.json'
VIEW_ID = '216595109'


def initialize_analyticsreporting():
  """Initializes an Analytics Reporting API V4 service object.

  Returns:
    An authorized Analytics Reporting API V4 service object.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)

  # Build the service object.
  analytics = build('analyticsreporting', 'v4', credentials=credentials)

  return analytics


def get_report(analytics):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '2000daysAgo', 'endDate': 'today'}],
          'metrics': [{'expression': 'ga:uniquePageviews'}],
          'dimensions': [{'name': 'ga:pagePath'}]
        }]
      }
  ).execute()


def get_report_most_popular(analytics):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '14daysAgo', 'endDate': 'today'}],
          'metrics': [{'expression': 'ga:uniquePageviews'}],
          'dimensions': [{'name': 'ga:pagePath'}]
        }]
      }
  ).execute()

def get_report_events(analytics, event_action):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '2000daysAgo', 'endDate': 'today'}],
          'metrics': [{'expression': 'ga:totalEvents'}],
          'dimensions': [{'name': 'ga:eventAction'}]
        }]
      }
  ).execute()


def get_report_pageviews(analytics):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '2000daysAgo', 'endDate': 'today'}],
          'metrics': [{'expression': 'ga:pageviews'}],
          'dimensions': [{'name': 'ga:pagePath'}]
        }]
      }
  ).execute()


def print_response(response):
  """Parses and prints the Analytics Reporting API V4 response.

  Args:
    response: An Analytics Reporting API V4 response.
  """
  total = 0
  pageslist = []
  pageviewslist = []

  for report in response.get('reports', []):
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])

    for row in report.get('data', {}).get('rows', []):
      dimensions = row.get('dimensions', [])
      dateRangeValues = row.get('metrics', [])

      for header, dimension in zip(dimensionHeaders, dimensions):
        pageslist.append(dimension)

      for i, values in enumerate(dateRangeValues):
        for metricHeader, value in zip(metricHeaders, values.get('values')):
          total += int(value)
          pageviewslist.append(int(value))

  dict_list = []

  for i in range(len(pageslist)):
    pages_dict = {'page': pageslist[i], 'views': pageviewslist[i]}
    dict_list.append(pages_dict)

  newlist = sorted(dict_list, key=itemgetter('views'), reverse=True)

  return newlist


def main():
  analytics = initialize_analyticsreporting()
  response = get_report(analytics)
  print_response(response)

if __name__ == '__main__':
  main()