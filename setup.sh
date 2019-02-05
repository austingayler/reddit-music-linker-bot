#for sql
sudo apt -y  install libicu-dev

# for Selenium
wget -q -O - "https://dl-ssl.google.com/linux/linux_signing_key.pub" | sudo apt-key add -

sudo apt-get update
sudo apt-get -y install google-chrome-stable
sudo apt-get -y install xvfb
sudo apt-get -y install unzip

wget https://chromedriver.storage.googleapis.com/2.32/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm chromedriver_linux64.zip
