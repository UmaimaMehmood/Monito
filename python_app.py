import urllib.request

print("This is a site connectivity checker program")

def main(url):
    print("Checking connectivity...")
    try:
        response = urllib.request.urlopen(url)
        print("Connected to", url, "successfully")
        print("The response code was:", response.getcode())
    except Exception as e:
        print("Error:", e)

input_url = input("Input the url of the site you want to check: ")
main(input_url)
