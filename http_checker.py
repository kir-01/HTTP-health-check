import sys
import yaml
import requests
import time

def read_config(file_path):
    try:
        with open(file_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error while parsing YAML in the configuration file: {e}")
        sys.exit(1)

def initialize_domain_history(endpoints):
   # Initialize an empty dictionary to store the history of UP and DOWN counts for each main domain.
    domain_history = {}

    # Iterate through each endpoint in the list of endpoints.
    for endpoint in endpoints:
        # Extract the main domain from the endpoint's URL.
        main_domain = get_main_domain(endpoint['url'])
        # Create an entry in the dictionary for the main domain with initial counts of 'UP' and 'DOWN' set to 0.
        domain_history[main_domain] = {'UP': 0, 'DOWN': 0}

    return domain_history

def update_domain_history(domain_history, url, is_up):
    # Update the UP and DOWN counters for the specified domain
    main_domain = get_main_domain(url)
    if is_up:
        domain_history[main_domain]['UP'] += 1
    else:
        domain_history[main_domain]['DOWN'] += 1

def calculate_availability(domain_history):
    # Calculate and return the availability percentage for each domain
    availability_percentages = {}
    for domain, counters in domain_history.items():
        total_requests = counters['UP'] + counters['DOWN']
        availability_percentage = (counters['UP'] / total_requests) * 100 if total_requests > 0 else 0
        availability_percentages[domain] = availability_percentage
    return availability_percentages

def health_check(endpoints, domain_history):
    for endpoint in endpoints:
        try:
            method = endpoint.get('method', 'GET')
            url = endpoint['url']
            headers = endpoint.get('headers', {})
            body = endpoint.get('body', None)

            start_time = time.time()
            
            response = requests.request(method, url, headers=headers, data=body, timeout=60)

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            is_up = response.status_code // 100 == 2 and latency < 500

            update_domain_history(domain_history, url, is_up)

            if is_up:
                print(f"Successful request to {url} with latency: {latency:.2f} ms")
            else:
                print(f"Unsuccessful request to {url} - Status Code: {response.status_code}, Latency: {latency:.2f} ms")

        except requests.RequestException as e:
            update_domain_history(domain_history, url, False)
            print(f"Error while making the request: {e}")

def get_main_domain(url):
    # Remove the scheme (http:// or https://) if present
    url_without_scheme = url.split("://", 1)[1]

    # Split the URL by '/' to get the domain part
    domain_parts = url_without_scheme.split("/", 1)
    main_domain = domain_parts[0]

    # Remove any port number if present
    main_domain = main_domain.split(":")[0]

    return main_domain

def parseymlfile(config_file_path):
    config = read_config(config_file_path)
    domain_history = initialize_domain_history(config)

    while True:
        health_check(config, domain_history)
        availability_percentages = calculate_availability(domain_history)
        print("Availability Percentages:")
        for domain, percentage in availability_percentages.items():
            print(f"{domain}: {percentage:.2f}%")

        # Sleep for 15 seconds before the next test cycle
        time.sleep(15)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Enter the <config_file_path>")
        sys.exit(1)
    
    config_file_path = sys.argv[1]
    parseymlfile(config_file_path)
