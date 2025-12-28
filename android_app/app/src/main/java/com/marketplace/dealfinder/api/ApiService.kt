package com.marketplace.dealfinder.api

import com.marketplace.dealfinder.models.Deal
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("api/register")
    suspend fun registerDevice(@Body request: Map<String, Any>): Response<RegisterResponse>

    @POST("api/update_location")
    suspend fun updateLocation(@Body request: Map<String, Any>): Response<GenericResponse>

    @POST("api/feedback")
    suspend fun submitFeedback(@Body request: Map<String, Any>): Response<FeedbackResponse>

    @GET("api/deals")
    suspend fun getDeals(@Query("device_id") deviceId: String? = null): Response<DealsResponse>

    @GET("health")
    suspend fun healthCheck(): Response<HealthResponse>
}

data class RegisterResponse(
    val status: String,
    val message: String,
    val device_id: String
)

data class GenericResponse(
    val status: String,
    val message: String
)

data class FeedbackResponse(
    val status: String,
    val message: String,
    val model_stats: Map<String, Any>?
)

data class DealsResponse(
    val status: String,
    val count: Int,
    val deals: List<Deal>
)

data class HealthResponse(
    val status: String,
    val timestamp: String,
    val ml_model_stats: Map<String, Any>?
)
