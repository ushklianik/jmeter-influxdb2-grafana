# InfluxDB Backend Listener for Apache JMeter
Implementation of Apache JMeter BackendListenerClient for needs of the EPAM's client-side performance monitoring.

Plugin writes sample results to InfluxDB.


## Installation
Build plugin with `maven package`.

Copy `jmeter-influxdb-listener-for-client-side-{version}.jar` into `$JMETER_HOME/lib/ext` directory


## Enable sending data to InfluxDB
You can control whether to send sample results to InfluxDB by setting the following JMeter property:
```
clientside.influx.out.enabled=true
```
If this property is not set or set to `false`, Backend Listener will not send any results to database.


## Dependencies
Plugin requires the following libraries to be in Java classpath (to be placed into `$JMETER_HOME/lib`):
```
converter-moshi-2.6.2.jar
influxdb-java-2.17.jar
logging-interceptor-3.14.4.jar
moshi-1.8.0.jar
okhttp-3.14.4.jar
okio-1.17.2.jar
retrofit-2.6.2.jar
```