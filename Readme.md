# Startup commands
git clone https://github.com/Maadi5/ToodlesAPIs.git
sudo apt install -y python3 python3-venv python3-pip
python3 -m venv venv
source venv/bin/activate
cd ToodlesAPIs
pip install -r requirements.txt

# Replace config file with correct values
cp config.py.template config.py

# Use the following commands to enable the service
sudo cp ./toodles.service /etc/systemd/system/toodles.service
sudo sytemctl start toodles.service
sudo systemctl enable toodles.service


ops goes to ec2 turns on the server
browntape is where the order begins -> ops uploads some magic csv from here to the ec2 swagger

the following script executes
orders_csv_postapi -> receives the browntape payload and pushes to googles sheets daatabasse

eveery 3 hours, delivery tracking cron - delivery_tracker_cron
works out of the database google sheet. 

wati_apis.py -> whenever ops wants to updates the wati contact list. Update some tags 


