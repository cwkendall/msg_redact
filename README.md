## Twilio Message Redaction

A simple command line script (written in Python) for redacting messages stored on Twilio

It supports selection of messages to be processed either by date range, the phone numbers involved or directly by sid.
For more info consult the online help with `--help`

### Installation and Usage

The script requires Python 3 to run.

Setup your environment to include `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` variables

`Pipenv` is recommended to automatically handle your Python virtual environment
It can also automatically source a `.env` file to configure the shell inside the virtual environment

on MacOS (be sure to replace xxxxxxxxxxxxxxxx with your account credentials):
```
cat "export TWILIO_ACCOUNT_SID=xxxxxxxxxxxxxxx; export TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxx;" > .env

brew install python3 pipenv
pipenv install
pipenv run ./msg_redact.py [OPTIONS]

```
