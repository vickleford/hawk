Watch your servers like a hawk with Rackspace Cloud Monitoring.

The primary goal of hawk is to ease the setup of your checks and alarms in Rackspace Cloud Monitoring by translating the API documentation specs into YAML.

## Installation

Sorry, not available over PyPI yet ;(

Just grab it from GitHub and install it.

	$ git clone https://github.com/vickleford/hawk
	...
    $ python setup.py install
    
Alternatively, you could do this inside a virutal environment.

	$ git clone https://github.com/vickleford/hawk
	...
	$ virtualenv hawk
	...
	$ cd hawk
	$ python setup.py install
    
## Configuration: Checks and Alarms

As stated above, the main goal is to translate the API documentation for checks and alarms to YAML. These checks and alarms are divided up into different "profiles" in YAML, by which you can collectively apply a secion of checks and alarms to a certain type of server. The profile names are arbitrary, so use what makes sense to you. Examples are "base", "search" for my ElasticSearch nodes, "nosql" for my MongoDB nodes, etc...

Hawk looks for that config file at ~/.config/hawk.yaml

Here are the places in the docs where you should be particularly interested:

* [Remote Check Types](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types-remote.html)
* [Agent Check Types](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types-agent.html)
* [Check Attributes](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-checks.html#swiz-checks.xml)
* [Alarm Attributes](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-alarms.html#swiz-alarms.xml)
* [Alerts DSL](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/alerts-language.html)

As an example, the API documentation lists attributes for creating a check: type (required), label (optional but recommended), period (optional), and details (optional but required for some types of checks). These are attributes every check gets. 

If we wanted to create a CPU check, we would follow the API docs to Agent Check Types to find out what details go into our CPU check. There are no additional attributes specific to CPU checks, so we can omit the details section. Our YAML would begin to look something like:

    profile_name:
        checks:
            arbitrary_check_name:
                type: agent.cpu
                label: "A human friendly label for a CPU check"
                period: 30
                
By that same standard, if we wanted to create an agent.disk check, which does have specific attributes to that type of check, our YAML could be extended to look like:

    profile_name:
        checks:
            arbitrary_check_name:
                type: agent.cpu
                label: "A human friendly label for a CPU check"
                period: 30
            arbitrary_disk_check_name:
                type: agent.disk
                label: "A human friendly label for a disk check"
                period: 30
                details:
                    target: /dev/xvda1
                    
The same exact principle can be used for alarms. When creating alarms, match the arbitrary alarm name to the arbitrary check name for that check you defined in the YAML. This is how hawk knows which alarm to associate with which checks especially when creating checks and alarms across multiple enities.

If we wanted to receive an alarm notification when our CPU usage exceeded 90%, we could do something like this:

    profile_name:
        checks:
            arbitrary_check_name:
                type: agent.cpu
                label: "A human friendly label for a CPU check"
                period: 30
            arbitrary_disk_check_name:
                type: agent.disk
                label: "A human friendly label for a disk check"
                period: 30
                details:
                    target: /dev/xvda1
        alarms:
            arbitrary_check_name:
                label: "CPU Alarm"
                criteria: |
                    if (metric['usage_average'] >= 90) {
                        return new AlarmStatus(WARNING, "Overall CPU usage higher than 90%!");
                    }
                    return new AlarmStatus(OK)
                    
The alarm DSL is much simpler than it looks. The trick is to realize your choices for metrics are defined by each check type. For example, at the [Agent Check Types for CPU Checks](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/appendix-check-types-agent.html#section-ct-agent.cpu) page in the API documentation, we can see some our options (under metrics) are: max_cpu_usage, min_cpu_usage, user_percent_average, ..., usage_average (Table B.29. Metrics). 

See the Alarms DSL section in the API documentation for more information. 

Hawk provides a sample configuration file as hawk_sample.yaml. Feel free to use it to get started or just use it as a quick reference guide.

CAVEAT: The rackspace-monitoring library does a great job of doing a direct translation for everyting straight to the API with one exception: the API docs need "monitoring_zones_poll" for remote checks, but rackspace-monitoring uses "monitoring_zones". Be sure to specify "monitoring_zones" in your remote checks in hawk.yaml.

## Configuration: Adding Accounts

Hawk needs to know about your Rackspace Cloud accounts before you can begin using it. There are two ways to add (or update) accounts.

Interactively: 

	$ hawk account_name1 passwd
	API Key: 
	$

Non-interactively:

	$ hawk account_name1 passwd -p password_string
	$

## Custom Notifications

If not given a notification plan to use, hawk will use the account default: npTechnicalContactsEmail. If you wish to customize your notifications, you can do so by creating notifications then creating a notification plan detailing what notifications to run in different alarm states. Notifications and notification plans can be used by all entities on an account.

To view all notifications and notification plans available to you, 

    hawk account_name1 list-notifications
    
Notice how notification plans are made up of notifications.

### Notifications

To create a notification, choose between 3 types: email, pagerduty, or webhook. Unfortunately, the usage of pagerduty wasn't clear at the time of this writing. 

    hawk account_name1 create-notification label email team@example.org

Example 2 with a webhook

    hawk account_name1 create-notification label webhook http://www.example.org/
    
When using webhook notifications, MaaS will POST to the URL you specify with interesting information about what happened. See the API documentation about [Notification Types](http://docs.rackspace.com/cm/api/v1.0/cm-devguide/content/service-notification-types-crud.html)
    
### Notification Plans

To create a notification plan, gather all the notification IDs (referenced as npX1, npX2, ... npXT) you want to include in the plan. Specify the desired notification IDs for the alarm statuses. Each status can contain multiple notification IDs and no two statuses need to contain the same IDs (but it may be a good idea to make them consistent).

hawk account_name1 create-notification-plan --ok npX1 --critical npX1 --warning npX1 some_label_name