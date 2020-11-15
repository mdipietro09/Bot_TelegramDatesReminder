
## Keys
#ENV = "DEV"
ENV = "PROD"

if ENV == "DEV":
	from settings import keys
	telegram_key = keys.telegram_key
	mongodb_key = keys.mongodb_key

elif ENV == "PROD":
	import ast
	telegram_key = ast.literal_eval(os.environ["telegram_key"])
	mongodb_key = ast.literal_eval(os.environ["mongodb_key"])


## fs
#import os
#root = os.path.dirname(os.path.dirname(__file__)) + "/"


## hosting
#import os
#port = int(os.environ.get("PORT", 5000))
#host = "0.0.0.0"
