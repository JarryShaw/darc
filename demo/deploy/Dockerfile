# use directly the existing image
FROM ghcr.io/jarryshaw/darc:latest

# add the source code into the image
COPY market /market/
COPY market.txt /market/text/

# change the entrypoint
ENTRYPOINT [ "python3", "/market/run.py" ]
