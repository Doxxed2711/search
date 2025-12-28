package com.marketplace.dealfinder.location

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Geocoder
import android.location.Location
import android.util.Log
import androidx.core.content.ContextCompat
import com.google.android.gms.location.*
import com.marketplace.dealfinder.api.ApiClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.*

class LocationManager(private val context: Context) {

    private val fusedLocationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)

    private val locationRequest = LocationRequest.Builder(
        Priority.PRIORITY_HIGH_ACCURACY,
        300000L // 5 minutes
    ).apply {
        setMinUpdateIntervalMillis(60000L) // 1 minute
        setMaxUpdateDelayMillis(600000L) // 10 minutes
    }.build()

    private val locationCallback = object : LocationCallback() {
        override fun onLocationResult(locationResult: LocationResult) {
            locationResult.lastLocation?.let { location ->
                onLocationChanged(location)
            }
        }
    }

    companion object {
        private const val TAG = "LocationManager"
    }

    fun startLocationUpdates() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED) {
            Log.e(TAG, "Location permission not granted")
            return
        }

        fusedLocationClient.requestLocationUpdates(
            locationRequest,
            locationCallback,
            null
        )

        // Get last known location immediately
        fusedLocationClient.lastLocation.addOnSuccessListener { location ->
            location?.let { onLocationChanged(it) }
        }

        Log.d(TAG, "Started location updates")
    }

    fun stopLocationUpdates() {
        fusedLocationClient.removeLocationUpdates(locationCallback)
        Log.d(TAG, "Stopped location updates")
    }

    private fun onLocationChanged(location: Location) {
        Log.d(TAG, "Location changed: ${location.latitude}, ${location.longitude}")

        // Reverse geocode to get city name and Craigslist area
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val geocoder = Geocoder(context, Locale.getDefault())
                val addresses = geocoder.getFromLocation(location.latitude, location.longitude, 1)

                if (!addresses.isNullOrEmpty()) {
                    val address = addresses[0]
                    val city = address.locality ?: address.subAdminArea ?: "Unknown"
                    val state = address.adminArea ?: ""

                    // Map to Craigslist area (simplified - you might want a better mapping)
                    val craigslistArea = getCraigslistArea(city, state)

                    // Send location to server
                    updateServerLocation(
                        latitude = location.latitude,
                        longitude = location.longitude,
                        city = city,
                        craigslistArea = craigslistArea
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error geocoding location", e)
            }
        }
    }

    private suspend fun updateServerLocation(
        latitude: Double,
        longitude: Double,
        city: String,
        craigslistArea: String
    ) {
        try {
            val deviceId = android.provider.Settings.Secure.getString(
                context.contentResolver,
                android.provider.Settings.Secure.ANDROID_ID
            )

            val request = mapOf(
                "device_id" to deviceId,
                "location" to mapOf(
                    "latitude" to latitude,
                    "longitude" to longitude,
                    "city" to city,
                    "craigslist_area" to craigslistArea
                )
            )

            val response = ApiClient.apiService.updateLocation(request)
            if (response.isSuccessful) {
                Log.d(TAG, "Location updated on server: $city ($craigslistArea)")
            } else {
                Log.e(TAG, "Failed to update location: ${response.code()}")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error updating location on server", e)
        }
    }

    private fun getCraigslistArea(city: String, state: String): String {
        // Simple mapping of major cities to Craigslist areas
        // You can expand this mapping or use a more sophisticated approach
        return when {
            city.contains("San Francisco", ignoreCase = true) ||
            city.contains("Oakland", ignoreCase = true) ||
            city.contains("San Jose", ignoreCase = true) -> "sfbay"

            city.contains("New York", ignoreCase = true) -> "newyork"
            city.contains("Los Angeles", ignoreCase = true) -> "losangeles"
            city.contains("Chicago", ignoreCase = true) -> "chicago"
            city.contains("Seattle", ignoreCase = true) -> "seattle"
            city.contains("Boston", ignoreCase = true) -> "boston"
            city.contains("Portland", ignoreCase = true) && state.contains("Oregon") -> "portland"
            city.contains("Austin", ignoreCase = true) -> "austin"
            city.contains("Denver", ignoreCase = true) -> "denver"
            city.contains("Phoenix", ignoreCase = true) -> "phoenix"
            city.contains("San Diego", ignoreCase = true) -> "sandiego"
            city.contains("Dallas", ignoreCase = true) -> "dallas"
            city.contains("Houston", ignoreCase = true) -> "houston"
            city.contains("Miami", ignoreCase = true) -> "miami"
            city.contains("Atlanta", ignoreCase = true) -> "atlanta"

            else -> "sfbay" // Default
        }
    }
}
