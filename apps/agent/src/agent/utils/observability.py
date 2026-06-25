"""Observability utilities for OpenTelemetry tracing."""

import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def configure_observability(app=None):
    """Configure OpenTelemetry tracing.
    
    Args:
        app: Optional FastAPI application to instrument.
    """
    # Create resource
    resource = Resource.create(attributes={
        "service.name": "university-agent-scaffold",
        "service.version": "0.1.0",
        "deployment.environment": os.getenv("AGENT_ENVIRONMENT", "development")
    })

    # Initialize TraceProvider
    provider = TracerProvider(resource=resource)
    
    # Export to console by default in dev, can be swapped for OTLP in prod
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)

    # Instrument FastAPI if provided
    if app:
        FastAPIInstrumentor.instrument_app(app)

def get_tracer(name: str):
    """Get an OpenTelemetry tracer.
    
    Args:
        name: Name of the tracer.
    """
    return trace.get_tracer(name)
