
service:
	uvicorn server.main:app --port 5001 --host 0.0.0.0 --reload

test:
	curl  -X POST \
		'http://localhost:5001/queries' \
		--header 'Content-Type: application/json' \
		--data-raw '{"sql":"select * from car_live_data"}'