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
