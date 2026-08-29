package io.github.macmacs.af.data;

import android.content.Context;
import android.util.Log;

import androidx.preference.PreferenceManager;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Locale;
import java.util.TimeZone;

import io.github.macmacs.af.BuildConfig;

/**
 * Debug-only mock for the network data sources. When the SharedPreferences key
 * {@link #PREF_MOCK_THEME} is set (only honoured in debug builds), every
 * {@code AfUtils.setupHttpClient()} call is served a deterministic, synthetic
 * response instead of hitting the network. Used by the screenshot capture
 * pipeline so screenshots render stable, curated data without an internet
 * connection.
 */
public class AfMockData {

	private static final String TAG = "AfMockData";

	public static final String PREF_MOCK_THEME = "global_mock_weather";

	public static final String THEME_COLD = "cold";
	public static final String THEME_WARM = "warm";
	public static final String THEME_BLACK = "black";
	public static final String THEME_ROUND = "round";

	private static final String MOCK_TIME_ZONE = "Europe/Berlin";
	private static final String MOCK_COUNTRY_CODE = "DE";

	public static boolean isEnabled(Context context) {
		if (!BuildConfig.DEBUG) return false;
		String theme = getTheme(context);
		return theme != null && !theme.isEmpty();
	}

	public static String getTheme(Context context) {
		return PreferenceManager.getDefaultSharedPreferences(context)
				.getString(PREF_MOCK_THEME, null);
	}

	public static HttpURLConnection createConnection(URL url, Context context) throws IOException {
		String theme = getTheme(context);
		if (theme == null || theme.isEmpty()) theme = THEME_COLD;

		String response;
		try {
			response = buildResponse(url, theme);
		} catch (JSONException e) {
			throw new IOException("Failed to build mock response", e);
		}

		byte[] body = response.getBytes(StandardCharsets.UTF_8);
		return new MockHttpConnection(url, body);
	}

	private static String buildResponse(URL url, String theme) throws JSONException {
		String path = url.getPath();

		if (path.contains("locationforecast")) {
			return buildForecastJson(theme).toString();
		} else if (path.contains("timezoneJSON")) {
			return new JSONObject()
					.put("timezoneId", MOCK_TIME_ZONE)
					.put("countryCode", MOCK_COUNTRY_CODE)
					.toString();
		} else if (path.contains("sunrise/3.0")) {
			return buildSunMoonJson(url).toString();
		} else if (path.contains("searchJSON")) {
			return new JSONObject()
					.put("geonames", new JSONArray()
							.put(new JSONObject()
									.put("name", "Berlin")
									.put("countryName", "Germany")))
					.toString();
		}

		Log.d(TAG, "Unhandled mock URL: " + url);
		return "{}";
	}

	private static JSONObject buildSunMoonJson(URL url) throws JSONException {
		String[] segments = url.getPath().split("/");
		String type = segments[segments.length - 1];
		String query = url.getQuery() != null ? url.getQuery() : "";
		String date = "";
		for (String param : query.split("&")) {
			if (param.startsWith("date=")) {
				date = param.substring("date=".length());
			}
		}

		JSONObject properties = new JSONObject();

		if ("sun".equals(type)) {
			properties.put("sunrise", new JSONObject().put("time", date + "T07:55+01:00"));
			properties.put("sunset", new JSONObject().put("time", date + "T17:15+01:00"));
			properties.put("solarnoon", new JSONObject().put("disc_centre_elevation", "39.8"));
		} else {
			properties.put("moonrise", new JSONObject().put("time", date + "T09:10+01:00"));
			properties.put("moonset", new JSONObject().put("time", date + "T21:40+01:00"));
			properties.put("moonphase", "0.53");
		}

		return new JSONObject().put("properties", properties);
	}

	private static JSONObject buildForecastJson(String theme) throws JSONException {
		float[] temperatures;
		String[] symbols;
		float[] precipitation;
		float[] wind;

		switch (theme) {
			case THEME_WARM -> {
				temperatures = new float[] {
						18, 17, 16, 16, 15, 15, 16, 18, 20, 22, 24, 25,
						26, 27, 27, 26, 25, 24, 22, 21, 20, 19, 18, 18 };
				symbols = new String[] {
						"clearsky", "clearsky", "clearsky", "clearsky", "fair", "fair", "fair", "fair",
						"partlycloudy", "partlycloudy", "fair", "clearsky", "clearsky", "partlycloudy",
						"fair", "fair", "clearsky", "clearsky", "clearsky", "clearsky", "clearsky",
						"clearsky", "clearsky", "clearsky" };
				precipitation = new float[24];
				wind = new float[] { 2, 2, 2, 2, 2, 2, 2, 3, 3, 4, 4, 4, 5, 5, 4, 4, 4, 3, 3, 3, 3, 2, 2, 2 };
			}
			case THEME_BLACK -> {
				temperatures = new float[] {
						11, 11, 10, 10, 10, 10, 10, 11, 11, 12, 12, 13,
						13, 14, 14, 13, 13, 12, 12, 11, 11, 10, 10, 10 };
				symbols = new String[] {
						"rain", "rain", "heavyrain", "rain", "rainshowers", "heavyrain", "rain", "rain",
						"rainshowers", "rain", "heavyrain", "rainshowers", "rain", "rain", "heavyrain",
						"rainshowers", "rain", "heavyrain", "rain", "rainshowers", "rain", "rain",
						"heavyrain", "rain" };
				precipitation = new float[] {
						2.0f, 1.5f, 3.5f, 2.0f, 1.8f, 4.0f, 2.2f, 1.6f, 2.8f, 2.0f, 3.2f, 2.4f,
						2.0f, 1.9f, 3.6f, 2.6f, 2.0f, 3.4f, 2.0f, 2.5f, 2.1f, 1.8f, 3.0f, 2.0f };
				wind = new float[] {
						9, 10, 12, 11, 10, 12, 13, 14, 13, 12, 14, 15,
						14, 13, 14, 12, 11, 12, 11, 10, 11, 12, 11, 10 };
			}
			case THEME_ROUND -> {
				temperatures = new float[] {
						13, 13, 12, 12, 11, 11, 12, 13, 14, 15, 16, 17,
						18, 18, 17, 17, 16, 15, 14, 14, 13, 13, 12, 12 };
				symbols = new String[] {
						"cloudy", "cloudy", "fog", "fog", "fog", "cloudy", "partlycloudy", "partlycloudy",
						"fair", "fair", "partlycloudy", "partlycloudy", "cloudy", "partlycloudy", "fair",
						"fair", "partlycloudy", "cloudy", "lightrain", "lightrain", "cloudy", "cloudy",
						"cloudy", "cloudy" };
				precipitation = new float[] {
						0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
						0, 0, 0, 0, 0, 0, 0.3f, 0.5f, 0.2f, 0, 0, 0 };
				wind = new float[] { 3, 3, 2, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5, 4, 4, 3, 3, 4, 4, 3, 3, 3, 3 };
			}
			default -> { // cold
				temperatures = new float[] {
						-5, -6, -6, -7, -7, -7, -6, -5, -4, -3, -2, -1,
						0, 0, -1, -2, -3, -3, -4, -4, -5, -5, -6, -6 };
				symbols = new String[] {
						"clearsky", "clearsky", "partlycloudy", "cloudy", "snow", "snow", "snow",
						"lightsnow", "snowshowers", "snow", "lightsnow", "partlycloudy", "cloudy",
						"snowshowers", "snow", "lightsnow", "lightsnow", "cloudy", "cloudy",
						"partlycloudy", "clearsky", "clearsky", "clearsky", "clearsky" };
				precipitation = new float[] {
						0, 0, 0, 0, 0.6f, 0.8f, 1.2f, 0.9f, 0.5f, 0.4f, 0.3f, 0,
						0, 0.7f, 0.6f, 0.4f, 0.3f, 0, 0, 0, 0, 0, 0, 0 };
				wind = new float[] { 3, 3, 2, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6, 5, 5, 4, 4, 3, 3, 3, 3, 2, 2 };
			}
		}

		TimeZone utcTimeZone = TimeZone.getTimeZone("UTC");
		SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US);
		dateFormat.setTimeZone(utcTimeZone);

		Calendar base = Calendar.getInstance(utcTimeZone);
		base.set(Calendar.MINUTE, 0);
		base.set(Calendar.SECOND, 0);
		base.set(Calendar.MILLISECOND, 0);

		Calendar expires = (Calendar) base.clone();
		expires.add(Calendar.HOUR, 12);

		JSONArray timeSeries = new JSONArray();

		for (int hour = 0; hour < 48; hour++) {
			int cycleHour = hour % 24;

			Calendar time = (Calendar) base.clone();
			time.add(Calendar.HOUR, hour);

			JSONObject instantDetails = new JSONObject()
					.put("air_temperature", temperatures[cycleHour])
					.put("relative_humidity", 60.0f + (cycleHour * 7) % 30)
					.put("air_pressure_at_sea_level", 1012.0f + ((cycleHour * 3) % 9))
					.put("wind_speed", wind[cycleHour])
					.put("wind_speed_of_gust", wind[cycleHour] + 3.0f)
					.put("wind_from_direction", 200.0f + ((cycleHour * 17) % 80));

			JSONObject next1Hours = new JSONObject()
					.put("summary", new JSONObject().put("symbol_code", symbols[cycleHour]))
					.put("details", new JSONObject()
							.put("precipitation_amount", precipitation[cycleHour])
							.put("precipitation_amount_min", precipitation[cycleHour] * 0.7f)
							.put("precipitation_amount_max", precipitation[cycleHour] * 1.3f));

			JSONObject data = new JSONObject()
					.put("instant", new JSONObject().put("details", instantDetails))
					.put("next_1_hours", next1Hours);

			timeSeries.put(new JSONObject()
					.put("time", dateFormat.format(time.getTime()))
					.put("data", data));
		}

		return new JSONObject().put("properties", new JSONObject()
				.put("meta", new JSONObject()
						.put("updated_at", dateFormat.format(base.getTime()))
						.put("expires", dateFormat.format(expires.getTime())))
				.put("timeseries", timeSeries));
	}

	private static class MockHttpConnection extends HttpURLConnection {

		private final byte[] mBody;
		private InputStream mInputStream;

		MockHttpConnection(URL url, byte[] body) {
			super(url);
			mBody = body;
		}

		@Override
		public void disconnect() {
		}

		@Override
		public boolean usingProxy() {
			return false;
		}

		@Override
		public void connect() {
			mInputStream = new ByteArrayInputStream(mBody);
		}

		@Override
		public int getResponseCode() {
			return HTTP_OK;
		}

		@Override
		public InputStream getInputStream() {
			if (mInputStream == null) {
				connect();
			}
			return mInputStream;
		}

		@Override
		public String getContentEncoding() {
			return null;
		}
	}
}
