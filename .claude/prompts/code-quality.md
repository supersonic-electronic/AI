# Code Quality and Refactoring Prompts

## Fix Technical Debt

```
Address the following technical debt items in the AI portfolio optimization codebase:

1. **Dependency Management**:
   - Fix duplicate dependency declarations in pyproject.toml
   - Resolve version conflicts between project.dependencies and tool.poetry.dependencies
   - Add missing development dependencies (pytest, coverage tools)
   - Update outdated package versions while maintaining compatibility

2. **Type Safety**:
   - Add comprehensive type hints to all public APIs
   - Fix missing return type annotations in src/ingestion/ modules
   - Add proper generic types for container classes
   - Use Protocol classes for dependency injection interfaces

3. **Error Handling**:
   - Implement proper exception hierarchies for each module
   - Add timeout and retry logic for external API calls
   - Create graceful degradation when optional services are unavailable
   - Add input validation with meaningful error messages

4. **Configuration Issues**:
   - Add project description and metadata to pyproject.toml
   - Implement configuration schema validation with JSON Schema
   - Add environment variable validation and documentation
   - Create configuration templates for different deployment environments

5. **Code Organization**:
   - Remove or implement the empty main.py file
   - Fix inconsistent import ordering across modules
   - Remove unused imports and dead code
   - Standardize docstring format across all modules

6. **Logging Improvements**:
   - Add structured logging with correlation IDs
   - Implement log level configuration per module
   - Add performance logging for expensive operations
   - Create log aggregation and monitoring setup

Follow existing code patterns, maintain backward compatibility, and include comprehensive tests for all changes.
```

## Implement Async Processing

```
Refactor the document processing pipeline to use async/await patterns for improved performance and scalability:

1. **Core Async Refactoring**:
   - Convert PDFIngestor to async operations with aiofiles
   - Implement async batch processing for embeddings
   - Add async support for vector database operations
   - Create async job queues for long-running tasks

2. **Concurrency Patterns**:
   - Use asyncio.gather() for parallel document processing
   - Implement semaphores for rate limiting API calls
   - Add async context managers for resource management
   - Use asyncio.Queue for producer-consumer patterns

3. **API Integration**:
   - Convert OpenAI API calls to async using httpx
   - Implement async retry logic with exponential backoff
   - Add async circuit breaker pattern for external services
   - Create async connection pooling for database operations

4. **CLI Compatibility**:
   - Maintain synchronous CLI interface using asyncio.run()
   - Add progress tracking for async operations
   - Implement graceful cancellation for long-running tasks
   - Preserve existing command-line argument handling

5. **Error Handling**:
   - Implement proper async exception handling
   - Add timeout support for all async operations
   - Create async-safe logging and monitoring
   - Handle task cancellation gracefully

6. **Testing**:
   - Add pytest-asyncio for async test support
   - Create async test fixtures and mocks
   - Test concurrent operation scenarios
   - Add performance benchmarks for async vs sync operations

Maintain backward compatibility with existing synchronous interfaces while providing async alternatives for better performance.
```

## Add Monitoring and Observability

```
Implement comprehensive monitoring and observability for the AI portfolio optimization system:

1. **Structured Logging**:
   - Add correlation IDs for request tracing
   - Implement structured JSON logging with consistent schema
   - Add contextual logging with operation metadata
   - Create log aggregation and centralized logging setup

2. **Metrics Collection**:
   - Add Prometheus metrics for key operations
   - Track document processing performance and throughput
   - Monitor API call success rates and latency
   - Measure mathematical detection accuracy and performance

3. **Distributed Tracing**:
   - Implement OpenTelemetry for distributed tracing
   - Add trace spans for major operations
   - Track cross-service communication
   - Create trace correlation across async operations

4. **Health Checks**:
   - Add health check endpoints for all services
   - Monitor external service dependencies
   - Implement readiness and liveness probes
   - Create dependency health monitoring

5. **Alerting**:
   - Set up alerts for processing failures
   - Monitor API rate limits and quota usage
   - Alert on performance degradation
   - Create escalation policies for critical issues

6. **Dashboards**:
   - Create Grafana dashboards for system metrics
   - Add business metrics dashboards
   - Monitor resource usage and capacity
   - Track user activity and system usage patterns

7. **Performance Monitoring**:
   - Add APM (Application Performance Monitoring)
   - Track memory usage and garbage collection
   - Monitor database query performance
   - Profile CPU usage and bottlenecks

Include proper configuration management for monitoring settings and ensure minimal performance impact from observability overhead.
```

## Security Hardening

```
Implement comprehensive security measures for the AI portfolio optimization system:

1. **Input Validation and Sanitization**:
   - Add comprehensive input validation for all user inputs
   - Implement file upload security (type validation, size limits, virus scanning)
   - Sanitize mathematical formula inputs to prevent injection attacks
   - Validate configuration parameters and API inputs

2. **Authentication and Authorization**:
   - Implement JWT-based authentication for API endpoints
   - Add role-based access control (RBAC) for different user types
   - Create session management with secure session handling
   - Implement API key management and rotation

3. **API Security**:
   - Add rate limiting to prevent abuse
   - Implement CORS policies for web frontend
   - Add request/response validation middleware
   - Create API versioning and deprecation policies

4. **Data Protection**:
   - Encrypt sensitive data at rest (API keys, user data)
   - Implement secure data transmission (TLS/HTTPS)
   - Add data anonymization for logs and metrics
   - Create secure backup and recovery procedures

5. **Secret Management**:
   - Integrate with HashiCorp Vault or AWS Secrets Manager
   - Implement automatic secret rotation
   - Add secure environment variable handling
   - Create audit trails for secret access

6. **Security Monitoring**:
   - Add security event logging and monitoring
   - Implement intrusion detection and prevention
   - Monitor for suspicious activity patterns
   - Create security incident response procedures

7. **Compliance and Auditing**:
   - Add GDPR compliance features for document processing
   - Implement audit trails for all operations
   - Create data retention and deletion policies
   - Add compliance reporting and documentation

8. **Dependency Security**:
   - Add automated security scanning for dependencies
   - Implement vulnerability monitoring and patching
   - Use security-focused linting tools (bandit)
   - Create security testing in CI/CD pipeline

Follow security best practices and industry standards, include security testing, and document all security measures and procedures.
```
