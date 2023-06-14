import json
import slack
import requests

with open("block.json", "rt") as block_f:
    data = json.load(block_f)

def post_to_slack(message):
    webhook_url = "https://hooks.slack.com/services/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"
    slack_data = json.dumps({'blocks': message})
    res = requests.post(
        webhook_url, data=slack_data,
        headers={'Content-type': 'application/json'}
    )
    if res.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the resoponse is:\n%s'
            % (res.status_code, res.text)
        )

post_to_slack(data)


