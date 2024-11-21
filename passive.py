import os
from bs4 import BeautifulSoup
import ipaddress
import sys
import requests
import re
import geocoder


def search_full_name(full_name):
    # Préparer le résultat avec des valeurs par défaut
    result = {
        "First name": full_name.split(" ")[0],
        "Last name": full_name.split(" ")[1],
        "Address": None,
        "Number": None,
    }
    
    # Préparer l'URL et les en-têtes avec un User-Agent
    first_name, last_name = full_name.split()
    url = f"https://www.whitepages.be/Search/Person/?what={first_name}+{last_name}&where="
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }

    # Envoyer la requête HTTP
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"HTTP Error: {response.status_code}"}

    # Décoder le contenu HTML
    html_content = response.content.decode("utf-8")

    # Rechercher l'adresse dans le contenu HTML
    match_address = re.search(r'class="wg-address">\s+([^<\r\n]+)', html_content)
    if match_address:
        result["Address"] = match_address.group(1)

    # Rechercher le numéro de téléphone dans le contenu HTML
    match_number = re.search(r"phone\D*(\+\d+)", html_content)
    if match_number:
        result["Number"] = match_number.group(1)

    return result

def search_ip_address(ip_address):
    try:
        # Tentative de récupération des informations
        location = geocoder.ip(ip_address)
    except Exception as e:
        # Gestion des exceptions si une erreur survient
        return {"Error": f"Failed to retrieve information for IP {ip_address}. Reason: {str(e)}"}

    # Extraction des informations si la récupération est réussie
    city = location.city if hasattr(location, "city") else "cannot find"
    isp = location.org if hasattr(location, "org") else "cannot find"
    latitude = location.latlng[0] if hasattr(location, "latlng") else "-"
    longitude = location.latlng[1] if hasattr(location, "latlng") else "-"
    
    return {
        "ISP": isp,
        "City": city,
        "Latitude": latitude,
        "Longitude": longitude
    }
def search_social_networks(username):
    user = username.split("@")[1]

    social_networks = {
        "Facebook": (f"https://www.facebook.com/{user}", 5),
        "Instagram": (f"https://www.instagram.com/{user}", 5),
        "Steam": (f"https://steamcommunity.com/id/{user}", 5),
        "Reddit": (f"https://www.reddit.com/user/{user}", 15),
        "Twitch": (f"https://www.twitch.tv/{user}", 15),
    }

    found_networks = {}

    for network, (url, attempts) in social_networks.items():
        response = requests.get(url)
        html_content = response.content.decode("utf-8")
        if any(keyword in html_content for keyword in ["userVanity", "username=", "personaname", "profileId", "channel="]):
            found_networks[network] = "yes"
        else:
            found_networks[network] = "no"
    return found_networks

def next_filename(filename):
    filename, extension = os.path.splitext(filename)
    index = 1
    while os.path.exists(f"{filename}{index}{extension}"):
        index += 1
    return f"{filename}{index}{extension}"

def save_results(results, filename):
    if not os.path.exists(filename):
        with open(filename, "w") as file:
            for key, value in results.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")
    else:
        new_filename = next_filename(filename)
        with open(new_filename, "w") as file:
            for key, value in results.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")
        return new_filename

def cmd_help():
    print("Welcome to passive v1.0.0\n")
    print("OPTIONS:")
    print("    -fn         Search with full-name")
    print("    -ip         Search with ip address")
    print("    -u          Search with username")

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--help" or len(sys.argv) != 3:
        cmd_help()
        return

    flag = sys.argv[1]
    search_input = sys.argv[2]

    if flag == "-fn":
        results = search_full_name(search_input)
        print(f"{results}")
        # print(f"First name: {results['First name']}")
        # print(f"Last name: {results['Last name']}")
        # print(f"Address: {results['Address']}")
        # print(f"Number: {results['Number']}")

        filename = save_results(results, "result.txt")
        print(f"Saved in {filename if filename else 'result.txt'}")
    elif flag == "-ip":
        try:
            ipaddress.ip_address(search_input)
        except ValueError:
            print("Error: Invalid IP address format")
            return
        try:
            results = search_ip_address(search_input)
    
            # Vérifier si une erreur a été retournée par la fonction
            if "Error" in results:
                print(f"Error: {results['Error']}")
            else:
                print(f"ISP: {results['ISP']}")
                print(f"City: {results['City']}")
                print(f"Lat/Lon: {results['Latitude']} / {results['Longitude']}")

                # Sauvegarde des résultats dans un fichier
                filename = save_results(results, "result.txt")
                print(f"Saved in {filename if filename else 'result.txt'}")

        except Exception as e:
            # Gestion des erreurs inattendues
            print(f"{str(e)}")
    elif flag == "-u":
        if not search_input.startswith("@"):
            print("Error: Username must start with '@'")
            return
        results = search_social_networks(search_input)

        for network, status in results.items():
            print(f"{network}: {status}")

        filename = save_results(results, "result.txt")
        print(f"Saved in {filename if filename else 'result.txt'}")
    else:
        cmd_help()
        return

if __name__ == "__main__":
    main()
