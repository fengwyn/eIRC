# Clean cache(s) and/or log(s)
echo "" > $(find . -type f | grep *log)
rm -r $(find . -type d | grep __pycache__)
