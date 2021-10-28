#!/bin/bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

wget -N http://chromedriver.storage.googleapis.com/84.0.4147.30/chromedriver_linux64.zip
apt install unzip
unzip chromedriver_linux64.zip
chmod +x chrmomedriver
sudo mv -f chromedriver /usr/local/share/chromedriver
sudo ln -s /usr/local/share/chromedriver /usr/local/bin/chromedriver
pip3 install selenium
pip3 install bs4
pip3 install pandas
apt-get install subversion
echo "Install successfully"

