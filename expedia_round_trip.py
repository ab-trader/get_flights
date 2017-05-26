import json
import requests
from lxml import html
from collections import OrderedDict
import argparse

def parse(city1, city2, flight1_date, flight2_date):
	for i in range(5):
		try:
			url = ("https://www.expedia.com/Flights-Search?&mode=search&trip=roundtrip"
                "&leg1=from:{0},to:{1},departure:{2}TANYT&leg2=from:{1},to:{0},departure:{3}TANYT"
                "&passengers=children:0,adults:1,seniors:0,infantinlap:Y".format(
                city1, city2, flight1_date, flight2_date))

			response = requests.get(url)
			parser = html.fromstring(response.text)
			json_data_xpath = parser.xpath("//script[@id='cachedResultsJson']//text()")
			raw_json =json.loads(json_data_xpath[0])
			flight_data = json.loads(raw_json["content"])

			flight_info  = OrderedDict() 
			lists=[]

			for i in flight_data['legs'].keys():
				total_distance =  flight_data['legs'][i]["formattedDistance"]
				exact_price = flight_data['legs'][i]['price']['totalPriceAsDecimal']

				departure_location_airport = 'PDX' #flight_data['legs'][i]['departureLocation']['airportLongName']
				departure_location_city = flight_data['legs'][i]['departureLocation']['airportCity']
				departure_location_airport_code = flight_data['legs'][i]['departureLocation']['airportCode']
				
				arrival_location_airport = 'MOW' #flight_data['legs'][i]['arrivalLocation']['airportLongName']
				arrival_location_airport_code = flight_data['legs'][i]['arrivalLocation']['airportCode']
				arrival_location_city = flight_data['legs'][i]['arrivalLocation']['airportCity']
				airline_name = flight_data['legs'][i]['carrierSummary']['airlineName']
				
				no_of_stops = flight_data['legs'][i]["stops"]
				flight_duration = flight_data['legs'][i]['duration']
				flight_hour = flight_duration['hours']
				flight_minutes = flight_duration['minutes']
				flight_days = flight_duration['numOfDays']

				if no_of_stops==0:
					stop = "Nonstop"
				else:
					stop = str(no_of_stops)+' Stop'

				total_flight_duration = "{0} days {1} hours {2} minutes".format(flight_days,flight_hour,flight_minutes)
				departure = departure_location_airport+", "+departure_location_city
				arrival = arrival_location_airport+", "+arrival_location_city
				carrier = flight_data['legs'][i]['timeline'][0]['carrier']
				plane = carrier['plane']
				plane_code = carrier['planeCode']
				formatted_price = "{0:.2f}".format(exact_price)

				if not airline_name:
					airline_name = carrier['operatedBy']
				
				timings = []
				for timeline in  flight_data['legs'][i]['timeline']:
					if 'departureAirport' in timeline.keys():
						departure_airport = timeline['departureAirport']['longName']
						departure_time = timeline['departureTime']['time']
						arrival_airport = timeline['arrivalAirport']['longName']
						arrival_time = timeline['arrivalTime']['time']
						flight_timing = {
											'departure_airport':departure_airport,
											'departure_time':departure_time,
											'arrival_airport':arrival_airport,
											'arrival_time':arrival_time
						}
						timings.append(flight_timing)

				flight_info={'stops':stop,
					'ticket price':formatted_price,
					'departure':departure,
					'arrival':arrival,
					'flight duration':total_flight_duration,
					'airline':airline_name,
					'plane':plane,
					'timings':timings,
					'plane code':plane_code
				}
				lists.append(flight_info)
			sortedlist = sorted(lists, key=lambda k: k['ticket price'],reverse=False)
			return sortedlist
		
		except ValueError:
			print "Rerying..."
			
		return {"error":"failed to process the page",}

if __name__=="__main__":
	argparser = argparse.ArgumentParser()
	argparser.add_argument('city1', help = 'City 1 airport code')
	argparser.add_argument('city2', help = 'City 2 airport code')
	argparser.add_argument('flight1_date', help = 'MM/DD/YYYY')
	argparser.add_argument('flight2_date', help = 'MM/DD/YYYY')

	args = argparser.parse_args()
	city1 = args.city1
	city2 = args.city2
	flight1_date = args.flight1_date
	flight2_date = args.flight2_date
	print "Fetching flight details for %s <---> %s" % (city1, city2)
	scraped_data = parse(city1, city2, flight1_date, flight2_date)
	print "Writing data to output file"
	with open('%s-%s-flight-results.json' % (city1, city2), 'w') as fp:
	 	json.dump(scraped_data, fp, indent = 4)
