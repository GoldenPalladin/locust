# Locust-based load framework

## Links
https://docs.locust.io/en/stable/index.html

## Quickstart

* Implement API client and resources, use already existing doctors, technicans etc. from 
BDD test configs
* Don't forget to implement .healthcheck in API client to get the current 
version of API tested

        api.py:
            
        class APIClient(BaseAPI):
        
            def healthcheck(self):
                return self.client.get('admin/healthcheck').response

* Create a locustfile.py with test scenario
* Create a config for your test and add it to loadtest_registry.yml
* Use prepare_lambda.py to (create lambda and) upload load generator into lambda in required 
region
* Set up Sfx dashboard to collect required metrics from test and SUT [like this](https://app.signalfx.com/#/dashboard/EQgtwalAcAE?toDashboard=EQgtwalAcAE&mode=graph&groupId=EQgtvh6AgAA&configId=EQgtwbhAYAA&startTimeUTC=1584447341000&endTimeUTC=1584471720000)
* Set up profile.yml for test load level
* Start your test with load_test.py
* Enjoy


# Configuration

1. Create loadtest config **tests\_your_API_name\profile.yml**
2. Add your config into **config\loadtest_registry.yml**


### loadtest_registry.yml

Used to store list of test configs and pointing to the current test

    current: TPData
    
    registered:
      TPData:
        profile: tests/TPData/profile.yml

### profile.yml
Used for load test configuration. It has the following required sections:

    test_header:
      name: TPData        # name of the test and corresponding lambda-function
      description: Create and check treatment variants
      env: cs1            # env config filename to use in clients and endpoints
      location: us-west-2 # aws location to create and start test in
    
    profile:
      runner:
        # Valid formats for durations are: 20, 20s, 3m, 2h, 1h20m, 3h30m10s, etc.
        clients: 50       # maximum amount of clients executing load script (max load level)
        hatch_rate: 5     # clients per second, used in step load too
        duration: 3m      # overall test duration
        step_load: false  # true -- clients will be hatched in steps. No steps = clients/step_clients.
                          # false -- clients will be hatched continuously until 'client' level will be reached.
        step_duration: 2m # step duration, after step ends new step (and users hatch) will start
        step_clients: 150 # num clients to be hatched at step, after reaching this, load level will stay the same until step time ends
      test:
        locustfile: tests/TPData/locustfile.py #path to file with test script
        debug: false      # true -- script will be run in debug mode, normal is false
      logging:
        loglevel: INFO    # Choose between DEBUG/INFO/WARNING/ERROR/CRITICAL. Default is INFO.
        final_stats: false # true -- stats will be emitted by listeners only when test is ended
                          # false -- stats will be emitted periodically
        listeners: [Sfx, Splunk] #list of any in Sfx, Splunk, Debug
        hyperclient_console_log_level: CRITICAL # CRITICAL to avoid load generator console/logs flooding

_**Note:** clients are not equal to rps. If you're aiming at specific rps level, you'd better 
do some test launches to tune up clients amounts. In general task rps for TaskSequence can be
estimated as follows:_

             SUM_tasks[0...n] (wait_time + task_response time)    
    cients * ------------------------------------------------- 
                     wait_time + task_response_time
    
_For TaskSet tasks weights must be considered._


## BDD envs test data
BDD tests configs are used for API clients and resources. You should name it like **cs1.yml** and
specify its name in *test_header: env* section of *profile.yml* config.

# Writing tests

### Create API client and resources
In *framework/api/your_api_name* create your own api client and resources inherited 
from **Base.py**. You should implement all resource navigation logic inside the **resources.py**
class. This will allow to write tests in a way:

        self.client.treatment_variant.create(treatment_id=self.treatment_id,
                                treatment_variant_data=tvd,
                                adf=adf,
                                wcc=wcc) 

**Note:** API client **must** have .healthcheck implemented in order to save tested API version. 

### Create test script in locustfile.py

For detailed info [read the Locust documentation](https://docs.locust.io/en/stable/writing-a-locustfile.html).
Main points:
* Create child Locust class with client:


    class TPDataAPILocust(Locust):
        def __init__(self):
            super().__init__()
            self.client = TPDataAPIClient(config=env_config,
                                          creds=env_config.auto_system)
                                          
* Create test TaskSet or TaskSequence. TaskSequence will allow you to execute tasks in a sequence.
TaskSet will allow to balance task execution frequency with task weights.

_**Note:** It is better if each task has one transaction assertion._

* Create Locust user with task_set and wait_time


    class TPDataAPIUser(TPDataAPILocust):
        task_set = CheckTreatmentVariants
        wait_time = between(0.1, 0.2)
        

### Use Expected and Asserter classes

Use expected response class form **Expected.py** to assert if response has expected 
**response code**, contains **header** or **json** (as dict) or **text**, like this: 

        payload = {
            "iid": f'ids:{random.randint(0, 999999999):09}',
            "category": "xray:full-mouth",
            "access_policy": "allowAll",
            "tags": ['locust_test_tags'],
            "country_code": "US"
        }
        exp = ExpectedResponse(text='TreatmentVariant',
                               json=payload,
                               code=201)
**Note**: snake_case key namings of json/headers dicts will be converted to camelCase
namings to maintain json naming conventions

                           
Use **LocustAsserter** context manager to assert and record request results and timings:

        with LocustAsserter(expected=exp,
                            name='Get treatment variant') as transaction:
            transaction.response = self.client.{request_method}

#### Locust asserter options

* **expected** -- takes ExpectedResponse object to compare with. If response doesn't equal to expected, 
Locust request will be failed
* **name** -- transaction name to be displayed in results
* **interrupt_flow** -- all request Exceptions will be raised to TaskSequence level. If request doesn't
match expected, FlowException will be raised. This is required if we need sequential task execution,
e.g. create treatment and only after this create treatment variant -- to make Locust start the
whole TaskSequence over.
* **skip_transaction** -- if true, no request result and timings will be recorded in Locust statistics.
This is required when we need to do (and assert results) some data-preparation requests, but don't
care about their timings. 

## Set up configs
1. **profile.yml** -> profile -> test -> locustfile: _path to your locustfile_
2. **loadtest_registry.yml** -> registered -> _your_test_name_ -> profile: _path to profile.yml_
3. **loadtest_registry.yml** -> current -> _your_test_name_

## Check your test in debug mode
Debug mode allows to run code of your test once with 1 locust user, no repeat, no greenlets.
You can check in console if everything is ok. To start test in debug mode:
1. Set **profile.yml** -> profile -> test -> debug: true
2. Run **load_generator.py**                          
 
# Pushing tests to AWS

Tests are executed in AWS Lambda, which should be created for each region to be tested.
Test code with python packages is packed into .zip file. [More info on Lambdas](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)

### AWS credentials
A user with permissions to create and execute Lambda is created in account **align-invlgn-rnd-sqa-auto-dev**.
Credentials are stored in **system_credentials.yml**

### Creating and uploading tests

* In test **profile.yml** set **test_header: name** and **test_header: location** for Lambda
name and location
* Run **aws/prepare_lambda.py -b -u** to build and upload zip package to aws


    lambda.zip contents:
    -------------------
    [python-packages]
    [config]
    [framework]
    [tests]
    load_generator.py
* If Lambda doesn't exists, it will be created.

_**Note:** Required Python packages to run the tests are already built and stored in 
**aws\python-packages** folder. If there is a need to rebuild packages (e.g. you added new
dependency in project), you may use **-r** option. Packages will be rebuilt locally in Docker.
Linux docker container should be used. **lambda_requirements.txt** will be used for pip._

# Running test
1. **profile.yml** -> runner: set up test duration and load profile
2. Run **load_test.py**

_Under the hood it will split load test into 15 min intervals (which is maximum lambda execution
duration), calculate load profile for each interval and trigger lambda execution at appropriate 
time moments to maintain test integrity_

# Collecting test stats

## Listeners

Listeners are started in lambdas and are collecting and sending execution stats periodically 
or once before test is over:

    profile:
        logging:
            final_stats: false  # true -- stats will be emitted by listeners only when test is ended
                                # false -- stats will be emitted periodically


Stats emitting interval is configured in **systems_credentials.yml**:


      stats_interval: 5 #in seconds

### SignalFX
Signal FX listener collects the following stats as **gauges**:
* requests per second
* locust clients amount
* total requests sent
* total failed requests
* average response time

Stats are collected **per transaction name** (the one specified in Asserter) and 
 enriched with **test name** and **env** data.

**locust test start** and **locust test stop** events are triggered on load generator 
start and stop. **API names** and **API versions** are included in event dimensions.


Stats can be found by **locust.** prefix.

### Splunk
Failed requests are logged into splunk with all the exception details.
API names and API versions are included in error results.

### Percentille reports
Each lambda test stats are sent back to **load_test.py** script and then aggregated. 
Final percentille distribution can be printed into console or saved in .csv


# Structure

* **[aws]**:
  - **[python-packages]** -- folder with prebuild packages to run tests in Lambda
  - **lambda_requirements.txt** -- pip requirements to build *python-packages* for Lambda
  - **lambda.zip** -- lambda zip file with tests, framework and packages
  - **prepare_lambda.py** -- module to create *lambda.zip* and upload it to AWS
* **[config]**
  - **common.yml, cs1.yml** etc. -- API configs with already existing test data on envs
  - **env_config_reader.py** -- lib to import env test data configs
  - **loadtest_registry.yml** -- list of loadtest script files and configs, specifies which 
  test is current
  - **systems_credentials.yml** -- configs for Splunk, SFx, AWS
  - **test_config_reader.py** -- lib to import all configs into tests and framework
* **[framework]**
  - **[api]** -- folder for per-API wrappers for API clients and resources.
    - **[_your_API_]** -- ...
      - **api.py** -- subclass with API client
      - **resources.py** -- subclass with API resources
    - **base.py** -- base class for API and client
  - **[generator]** -- folder for load generator classes
    - **asserter.py** -- class to estimate resource response and save transaction as succeeded
     or failed
    - **debug.py** -- class for DebugRunner to run testscript in debug mode (1 locust user, 
    no repeat, no greenlets)
    - **expected.py** -- class to implement Expected response object (code, text, header 
    contents) to compare with actual response
    - **helpers.py** -- some lib for helper functions
    - **launcher.py** -- class to implement load test launcher
    - **listener.py** -- base class for test stats listener
    - **sfx.py** -- listener to emit stats to SFx
    - **splunk.py** -- listener to emit errors into splunk
  - **[test]** -- folder for load test classes
    - **interval.py** -- class to implement load change interval (used in lambda test 
    configuration)
    - **llp.py** -- class to implement load level point
    - **runner.py** -- dataclass for *runner* section of test config
    - **serialization.py** -- class for (de)serializing RequestStats object to pass it from 
    Lambda to test controller
    - **stats.py** -- module to implement some stats-transformation functions (console print, 
    cvs.export)
    - **stepload.py** -- dataclass for *stepload* section of configs
    - **timings.py** -- class to implement lambda triggering configs and timings
  - *settings.py** -- data class for test configs
* **[tests]** -- folder for test scripts and configs
  - **[_your_API_]** -- put your tests here
    - **locustfile.py** -- main file with load test scenario
    - **profile.yml** -- load test configuration
* **load_generator.py** -- Lambda event handler which triggers load test with passed settings and returns RequestStats object
* **load_test.py** -- main script to split test into consecutive/concurrent lambda executions, trigger them, 
collect and print test stats