package org.apache.jmeter.visualizers.backend.influxdb;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.apache.commons.lang3.StringUtils;
import org.apache.jmeter.config.Arguments;
import org.apache.jmeter.samplers.SampleResult;
import org.apache.jmeter.visualizers.backend.BackendListenerClient;
import org.apache.jmeter.visualizers.backend.BackendListenerContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.apache.jmeter.protocol.http.sampler.HTTPSampleResult;
import org.apache.jmeter.threads.JMeterContextService;
import org.apache.jmeter.threads.JMeterContextService.ThreadCounts;


public class InfluxDBRawBackendListenerClientV2 implements BackendListenerClient {

    private static final Logger log = LoggerFactory.getLogger(InfluxDBRawBackendListenerClientV2.class);

    private static final Object LOCK = new Object();

    private static final String TAG_OK = "ok";
    private static final String TAG_KO = "ko";
    private static final String DEFAULT_MEASUREMENT = "jmeter";

    private static final Map<String, String> DEFAULT_ARGS = new LinkedHashMap<>();

    static {
        DEFAULT_ARGS.put("influxdbMetricsSender", HttpMetricsSender.class.getName());
        DEFAULT_ARGS.put("influxdbUrl", "http://host_to_change:8086/api/v2/write?org=demo&bucket=demo");
        DEFAULT_ARGS.put("influxdbToken", "");
        DEFAULT_ARGS.put("measurement", DEFAULT_MEASUREMENT);
        DEFAULT_ARGS.put("testId", "");
        DEFAULT_ARGS.put("testProfile", "");
        DEFAULT_ARGS.put("batchSize", "200");
    }

    private InfluxdbMetricsSender influxDBMetricsManager;
    private String measurement;
    private String testId;
    private String testProfile;
    private int batchSize;
    private int currentBatchSize = 0;

    public InfluxDBRawBackendListenerClientV2() {
        // default constructor
    }

    /**
     * Used for testing.
     *
     * @param sender the {@link InfluxdbMetricsSender} to use
     */
    public InfluxDBRawBackendListenerClientV2(InfluxdbMetricsSender sender) {
        influxDBMetricsManager = sender;
    }

    @Override
    public void setupTest(BackendListenerContext context) throws Exception {
        initInfluxDBMetricsManager(context);
        measurement = context.getParameter("measurement", DEFAULT_MEASUREMENT);
        testId = context.getParameter("testId", "");
        testProfile = context.getParameter("testProfile", "");
        batchSize = context.getIntParameter("batchSize", 200);
    }

    private void initInfluxDBMetricsManager(BackendListenerContext context) throws Exception {
        influxDBMetricsManager = Class
                .forName(context.getParameter("influxdbMetricsSender"))
                .asSubclass(InfluxdbMetricsSender.class)
                .getDeclaredConstructor()
                .newInstance();

        influxDBMetricsManager.setup(
                context.getParameter("influxdbUrl"),
                context.getParameter("influxdbToken"));
    }

    @Override
    public void teardownTest(BackendListenerContext context) {
        influxDBMetricsManager.destroy();
    }

    @Override
    public void handleSampleResults(
            List<SampleResult> sampleResults, BackendListenerContext context) {
        log.debug("Handling {} sample results", sampleResults.size());
        currentBatchSize += sampleResults.size();
        synchronized (LOCK) {
            for (SampleResult sampleResult : sampleResults) {
                addMetricFromSampleResult(sampleResult);
            }
            if(currentBatchSize >= batchSize) {
                influxDBMetricsManager.writeAndSendMetrics();
                currentBatchSize = 0;
            }
        }
    }

    private void addMetricFromSampleResult(SampleResult sampleResult) {
        String tags = "," + createTags(sampleResult);
        String fields = createFields(sampleResult);
        long timestamp = sampleResult.getTimeStamp();

        influxDBMetricsManager.addMetric(measurement, tags, fields, timestamp);
    }

    private String createTags(SampleResult sampleResult) {
        boolean isError = sampleResult.getErrorCount() != 0;
        String status = isError ? TAG_KO : TAG_OK;
        // remove surrounding quotes and spaces from sample label
        String label = StringUtils.strip(sampleResult.getSampleLabel(), "\" ");
        String transaction = AbstractInfluxdbMetricsSender.tagToStringValue(label);
        String sample_type = "transaction";
        if (sampleResult instanceof HTTPSampleResult){
            sample_type = "request";
        }
        String result = "status=" + status
                + ",transaction=" + transaction
                + ",sample_type="+sample_type
                + ",testProfile="+testProfile
                + ",testId="+testId;

        if (sample_type == "request"){
            String responseCode = sampleResult.getResponseCode();
            if (responseCode.length() > 3){
                responseCode = responseCode.replaceAll("\\s+","_");
            }
            result = result + ",responseCode=" + responseCode;
        }
        return result;
    }

    private String createFields(SampleResult sampleResult) {
        ThreadCounts tc = JMeterContextService.getThreadCounts();
        long duration = sampleResult.getTime();
        long latency = sampleResult.getLatency();
        long connectTime = sampleResult.getConnectTime();
        int threads = tc.activeThreads;
        return "duration=" + duration
                + ",ttfb=" + latency
                + ",connectTime=" + connectTime
                + ",threads=" + threads;
    }

    @Override
    public Arguments getDefaultParameters() {
        Arguments arguments = new Arguments();
        DEFAULT_ARGS.forEach(arguments::addArgument);
        return arguments;
    }
}