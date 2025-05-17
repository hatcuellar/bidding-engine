"""
Observability utilities for the bidding engine.

This module provides OpenTelemetry and Prometheus instrumentation
for the FastAPI application.
"""

import os
import logging
from typing import Optional
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def setup_opentelemetry(app: FastAPI) -> None:
    """
    Set up OpenTelemetry instrumentation for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    try:
        # Only import OpenTelemetry if needed to avoid dependency issues
        from opentelemetry import trace
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource
        
        # Check if OTEL endpoint is configured
        otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        service_name = os.environ.get("OTEL_SERVICE_NAME", "bidding-engine-api")
        
        if not otel_endpoint:
            logger.info("OpenTelemetry endpoint not configured, skipping instrumentation")
            return
        
        # Set up tracer provider with the service name
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })
        
        tracer_provider = TracerProvider(resource=resource)
        
        # Set up the OTLP exporter
        otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Set the tracer provider
        trace.set_tracer_provider(tracer_provider)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)
        
        logger.info(f"OpenTelemetry instrumentation configured with endpoint: {otel_endpoint}")
    except ImportError as e:
        logger.warning(f"OpenTelemetry packages not available: {e}")
    except Exception as e:
        logger.error(f"Failed to configure OpenTelemetry: {e}")

def setup_prometheus(app: FastAPI) -> None:
    """
    Set up Prometheus metrics for the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    try:
        from prometheus_fastapi_instrumentator import Instrumentator, metrics
        
        # Create instrumentator
        instrumentator = Instrumentator()
        
        # Add default metrics
        instrumentator.add(metrics.latency())
        instrumentator.add(metrics.requests())
        instrumentator.add(metrics.requests_in_progress())
        instrumentator.add(metrics.dependency_latency())
        instrumentator.add(metrics.dependency_requests())
        
        # Add custom metrics for bidding engine
        from prometheus_client import Counter, Histogram
        
        # Counter for bids by type
        bids_by_type = Counter(
            name="bids_by_type_total",
            documentation="Total number of bids by type",
            labelnames=["bid_type"]
        )
        
        # Histogram for bid values
        bid_values = Histogram(
            name="bid_values",
            documentation="Distribution of bid values",
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0),
            labelnames=["bid_type"]
        )
        
        # Add custom metrics to collectors
        instrumentator.registry.register(bids_by_type)
        instrumentator.registry.register(bid_values)
        
        # Instrument app and expose metrics endpoint
        instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)
        
        logger.info("Prometheus metrics instrumentation configured")
        
        # Export metrics objects for use in the application
        return {
            "bids_by_type": bids_by_type,
            "bid_values": bid_values
        }
    except ImportError as e:
        logger.warning(f"Prometheus packages not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to configure Prometheus metrics: {e}")
        return None