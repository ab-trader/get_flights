import json
import requests
from lxml import html
from collections import OrderedDict
import argparse
import pandas as pd
import time

DELAY = 1
ATTEMPTS = 10
ATTEMPTS_DELAY = 5
DELAY_BTWN_REQUESTS = 30

def parse(city1, city2, flight1_date, flight2_date):

	for i in range(ATTEMPTS):
		try:
# DONE: change request to 1 adult and 2 kids
# TODO: add number and type of passengers into script parameters
			url = ("https://www.expedia.com/Flights-Search?&mode=search&trip=roundtrip"
                    "&leg1=from:{0},to:{1},departure:{2}TANYT&leg2=from:{1},to:{0},departure:{3}"
                    "TANYT&passengers=children:2[2;9],adults:1,seniors:0,infantinlap:Y".format(
                    city1, city2, flight1_date, flight2_date))

			response = requests.get(url)
			time.sleep(DELAY_BTWN_REQUESTS)

			response = requests.get(url)
			parser = html.fromstring(response.text)
			json_data_xpath = parser.xpath("//script[@id='cachedResultsJson']//text()")
			raw_json =json.loads(json_data_xpath[0])
			flight_data = json.loads(raw_json['content'])

			with open('flight-results-temp.json', 'w') as fp:
			    json.dump(flight_data, fp, indent = 4)

			flight_info  = OrderedDict() 
			lists=[]

			for i in flight_data['legs'].keys():

				exact_price = flight_data['legs'][i]['price']['totalPriceAsDecimal']
				no_of_stops = flight_data['legs'][i]['stops']

# TODO: decide what to do with commented areas

				#total_distance =  flight_data['legs'][i]['formattedDistance']
				#departure_location_city = \
    #                                flight_data['legs'][i]['departureLocation']['airportCity']
				#departure_location_airport_code = \
    #                                flight_data['legs'][i]['departureLocation']['airportCode']				
				#arrival_location_airport_code = \
    #                                flight_data['legs'][i]['arrivalLocation']['airportCode']
				#arrival_location_city = flight_data['legs'][i]['arrivalLocation']['airportCity']
				#airline_name = flight_data['legs'][i]['carrierSummary']['airlineName']
				#if airline_name == '': airline_name = 'Multiple'				
				#flight_duration = flight_data['legs'][i]['duration']
				#flight_hour = flight_duration['hours']
				#flight_minutes = flight_duration['minutes']
				#flight_days = flight_duration['numOfDays']

				if no_of_stops == 0:
					stop = 'Nonstop'
				else:
					stop = str(no_of_stops) + ' Stop'

				#total_flight_duration = "{0} days {1} hours {2} minutes".format(
    #                                                        flight_days,flight_hour,flight_minutes)
				#departure = departure_location_airport_code + ", " + departure_location_city
				#arrival = arrival_location_airport_code + ", " + arrival_location_city
				#carrier = flight_data['legs'][i]['timeline'][0]['carrier']
				#plane = carrier['plane']
				#plane_code = carrier['planeCode']

				#if not airline_name:
				#	airline_name = carrier['operatedBy']
				
				#timings = []
				#for timeline in  flight_data['legs'][i]['timeline']:

					#if 'departureAirport' in timeline.keys():
					#	departure_airport = timeline['departureAirport']['longName']
					#	departure_time = timeline['departureTime']['time']
					#	arrival_airport = timeline['arrivalAirport']['longName']
					#	arrival_time = timeline['arrivalTime']['time']
					#	flight_timing = {
					#						'departure_airport':departure_airport,
					#						'departure_time':departure_time,
					#						'arrival_airport':arrival_airport,
					#						'arrival_time':arrival_time
					#	}
					#	timings.append(flight_timing)

				formatted_price = "{0:.2f}".format(exact_price)
				flight_info = {'stops': stop,
					'ticket price': formatted_price,
					#'departure': departure,
					#'arrival': arrival,
					#'flight duration': total_flight_duration,
					#'airline': airline_name,
					#'plane': plane,
					#'timings': timings,
					#'plane code': plane_code
				}

				lists.append(flight_info)

			sortedlist = sorted(lists, key=lambda k: k['ticket price'], reverse=False)

			return sortedlist
		
		except ValueError:

			time.sleep(ATTEMPTS_DELAY)
			print "Retrying..."
			
		return {"error": "failed to process the page",}

if __name__=="__main__":
	argparser = argparse.ArgumentParser()
	argparser.add_argument('city1', help = 'City 1 airport code')
	argparser.add_argument('flight1_date', help = 'MM/DD/YYYY')
	argparser.add_argument('flight12_date', help = 'MM/DD/YYYY')
	argparser.add_argument('city2', help = 'City 2 airport code')
	argparser.add_argument('flight2_date', help = 'MM/DD/YYYY')
	argparser.add_argument('flight22_date', help = 'MM/DD/YYYY')

	args = argparser.parse_args()

	dates1 = pd.date_range(args.flight1_date, args.flight12_date)
	dates2 = pd.date_range(args.flight2_date, args.flight22_date)

	min_prices_stop1 = pd.DataFrame(index=dates1, columns=dates2)
	min_prices_stop2 = pd.DataFrame(index=dates1, columns=dates2)

	print "Fetching flight details for %s <---> %s" % (args.city1, args.city2)

	for i, date1 in enumerate(dates1):
		for j, date2 in enumerate(dates2):
			scraped_data = parse(args.city1, args.city2,
                                 date1.strftime('%m/%d/%Y'), date2.strftime('%m/%d/%Y'))
			prices_stop1 = []
			prices_stop2 = []
			min_prices_stop1.iloc[i][j] = 0.0
			min_prices_stop2.iloc[i][j] = 0.0

			if len(scraped_data) > 1:
			    for dataset in scraped_data:
			        if dataset['stops'] == '1 Stop':
			            prices_stop1.append(float(dataset['ticket price']))
			        else:
			            prices_stop2.append(float(dataset['ticket price']))

			        if len(prices_stop1) != 0: min_prices_stop1.iloc[i][j] = min(prices_stop1)
			        if len(prices_stop2) != 0: min_prices_stop2.iloc[i][j] = min(prices_stop2)

			print args.city1, args.city2, date1.strftime('%m/%d/%Y'), date2.strftime('%m/%d/%Y'), \
                  min_prices_stop1.iloc[i][j], min_prices_stop2.iloc[i][j]

		#print "Writing data to output file"
		#with open('%s-%s-flight-results.json' % (args.city1, args.city2), 'w') as fp:
		#	json.dump(scraped_data, fp, indent = 4)

	min_prices_stop1.to_csv('min_ticket_prices_1_stop_%s_%s.csv' % (args.city1, args.city2))
	min_prices_stop2.to_csv('min_ticket_prices_2_stops_%s_%s.csv' % (args.city1, args.city2))

	print min_prices_stop1
	print
	print min_prices_stop2