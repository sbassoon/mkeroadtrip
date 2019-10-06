import random
import math
import requests
import csv
from mastodon import Mastodon
from secrets import *


def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier


def get_city(apiKey,lat,lng):
    url=('https://maps.googleapis.com/maps/api/geocode/json?latlng={},{}&key={}'
         .format(lat,
                 lng,
                 apiKey)
         )
    try:
        response = requests.get(url)
        resp_json_payload = response.json()
        city = resp_json_payload['results'][0]['address_components'][2]['long_name']
        city2 = resp_json_payload['results'][0]['address_components'][3]['long_name']
        cities = [city, city2]
    except:
        print('ERROR: {},{}'.format(lat,lng))
        cities = "null"
    return cities


def get_street(apiKey, lat, lng, heading, SaveLoc):
    url=("https://maps.googleapis.com/maps/api/streetview?size=1200x800&fov=90&heading={}&pitch=10&location={},{}&key={}"
         .format(heading,
                 lat,
                 lng,
                 apiKey)
         )
    print(url)
    try:
        r = requests.get(url, allow_redirects=True)
        open(SaveLoc + 'sv.jpg', 'wb').write(r.content)
    except:
        print("ERROR: {},{}".format(lat,lng))
    return


def check_sv_availability(apiKey, lat, lng, heading):
    url=("https://maps.googleapis.com/maps/api/streetview/metadata?size=1200x800&source=outdoor&location={},{}&fov=90&heading={}&pitch=10&key={}"
         .format(lat,
                 lng,
                 heading,
                 apiKey)
         )
    try:
        response = requests.get(url)
        resp_json_payload = response.json()
        available = resp_json_payload['status']
        if available == "OK":
            available = True
            print('{},{} pano available'.format(lat,lng))
        else:
            print('{},{} failed with status {}'.format(lat,lng,available))
            available = False
    except:
        print('ERROR: {},{}'.format(lat,lng))
        available = False
    return available


def get_pano():
    west_boundary: float = -88.0708755
    east_boundary: float = -87.863814
    north_boundary: float = 43.19496125
    south_boundary: float = 42.92081435

    height = north_boundary - south_boundary
    width = abs(west_boundary) - abs(east_boundary)

    generated_height = random.uniform(0, height)
    generated_width = random.uniform(0, width)

    generated_height = round_half_up(generated_height, 4)
    generated_width = round_half_up(generated_width, 4)

    generated_height = generated_height + south_boundary
    generated_width = generated_width + west_boundary

    generated_height = round_half_up(generated_height, 4)
    generated_width = round_half_up(generated_width, 4)

    header = random.randint(0, 360)

    cities = get_city(GMAPS_KEY, generated_height, generated_width)

    if cities[1] == "Milwaukee":
        sv_available = check_sv_availability(GMAPS_KEY, generated_height, generated_width, header)

        if sv_available is True:
            get_street(GMAPS_KEY, generated_height, generated_width, header, FILE_LOC)
            print("Downloaded: {},{}: {}".format(generated_height, generated_width, cities))

            with open('log.csv', 'a', newline='') as csvfile:
                datawriter = csv.writer(csvfile, delimiter=',',
                                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                datawriter.writerow([str(generated_height)] + [str(generated_width)] + cities)

            return True, cities, generated_height, generated_width
        else:
            get_results = get_pano()
            return get_results
    else:
        print("{},{} not in Milwaukee: {}".format(generated_height, generated_width, cities))
        get_results = get_pano()
        return get_results


if __name__ == "__main__":
    data_results = get_pano()

    print(data_results)

    Mastodon.create_app(
        'mkeroadtrip',
        api_base_url='https://botsin.space/',
        to_file='pytooter_clientcred.secret'
    )

    mastodon = Mastodon(client_id="pytooter_clientcred.secret", api_base_url=MAST_API_URL)
    mastodon.log_in(MAST_EMAIL,MAST_PASS,to_file="pytooter_clientcred.secret")
    mastodon = Mastodon(access_token="pytooter_clientcred.secret", api_base_url=MAST_API_URL)
    media_id = mastodon.media_post(FILE_PATH,description="A photo of the {} neighborhood of Milwaukee, Wisconsin, near location {},{}."
                                   .format(data_results[1][0],
                                           data_results[2],
                                           data_results[3]))

    status = "An image from the {} neighborhood in Milwaukee, Wisconsin. Coordinates: {}, {}".format(data_results[1][0], data_results[2], data_results[3])
    print(status)

    mastodon.status_post(status,media_ids=media_id,language="English")