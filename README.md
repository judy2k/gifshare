GifShare
========

A command-line tool to upload images to S3, for sharing over IRC or whatever. Supports copying the image from the Web and file renaming.

Requirements
------------

* Python 2.7 (it might run on earlier versions)
* libmagic (install on OSX with `brew install libmagic`, or on debian/ubuntu with `sudo apt-get install file`
* An AWS account


Installation
------------

At the moment

* Run `pip install -r requirements.txt`
* Copy `gifshare` into your path somewhere.
* Create a file at ~/.gifshare - it should be an ini file, and should contain the following:

        [default]
        aws_access_id=<your-aws-access-id>
        aws_secret_access_key=<your-aws-secret-access-key>
        web_root=<http://your.s3.bucket.domain.name/>
        region=<aws-region-code>
        bucket=<your-bucket-name>


Usage
-----

Run `gifshare --help` for usage instructions.
