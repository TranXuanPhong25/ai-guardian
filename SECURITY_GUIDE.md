# Security Improvements Implementation Guide

This document describes the security improvements implemented in the AI Guardian project and how to use them.

## Quick Start

### Running Security Tests

```bash
# Run all security tests
cd backend
python test_runner.py security

# Run with output file
python test_runner.py security --output security_report.json

# Run quietly (only errors)
python test_runner.py security --quiet
```

### Running Performance Tests

```bash
# Run performance tests (requires server to be running)
python test_runner.py performance --url http://localhost:8000

# Run all tests
python test_runner.py all --output comprehensive_report.json
```

### Running Integration Tests

```bash
# Quick integration test
python integration_test.py
```

## Security Features Implemented

### 1. **Enhanced Authentication & Authorization**
- JWT token validation with proper error handling
- User ownership checks for resource access
- Secure session configuration

### 2. **Comprehensive Input Validation**
- File upload security (type, size, content validation)
- Input sanitization and length limits
- Path traversal protection
- XSS and injection prevention

### 3. **Rate Limiting**
- Token bucket algorithm implementation
- Endpoint-specific rate limits
- Suspicious activity detection
- Automatic cleanup to prevent memory leaks

### 4. **Security Headers**
- Complete security headers suite
- CORS configuration
- Content Security Policy
- XSS and clickjacking protection

### 5. **Monitoring & Logging**
- Centralized logging configuration
- Security event logging
- Health check endpoints
- Performance metrics

### 6. **Environment Security**
- Environment-specific configurations
- Secure credential management
- Configuration validation

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Security
SECRET_KEY=your-strong-random-secret-key-here
JWT_SECRET_KEY=your-jwt-specific-secret-here
ENVIRONMENT=development

# Security Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
MAX_FILE_SIZE=52428800
RATE_LIMIT_PER_MINUTE=60

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_guardian

# External Services
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-supabase-anon-key

# Azure OpenAI
deployment_name=your-deployment
model_name=gpt-4
azure_endpoint=https://your-resource.openai.azure.com/
openai_api_key=your-api-key
openai_api_version=2024-02-15-preview

# Weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-weaviate-key

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_ROOT_USER=your-root-user
MINIO_ROOT_PASSWORD=your-root-password

# Logging (optional)
LOG_FILE=/var/log/ai-guardian/app.log
SECURITY_LOG_FILE=/var/log/ai-guardian/security.log
LOG_LEVEL=INFO
```

### Production Security Checklist

Before deploying to production:

- [ ] Change all default passwords and keys
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper `ALLOWED_HOSTS` and `ALLOWED_ORIGINS`
- [ ] Enable HTTPS and set secure cookie flags
- [ ] Set up proper logging and monitoring
- [ ] Configure backup and recovery procedures
- [ ] Run comprehensive security tests
- [ ] Set up intrusion detection

## API Endpoints

### Health Checks

- `GET /health` - Basic health status
- `GET /health/detailed` - Comprehensive system check
- `GET /metrics` - System performance metrics

### Security Testing (Development Only)

- `GET /security/scan` - Run security scan (only in development)

## Security Testing

### Automated Security Scans

The project includes automated security testing:

1. **Bandit**: Static analysis for Python security issues
2. **Safety**: Dependency vulnerability scanning
3. **Secret Detection**: Scan for hardcoded secrets
4. **Environment Validation**: Check configuration security

### Manual Security Testing

#### Input Validation Testing

```python
# Test file upload validation
curl -X POST -F "file=@malicious.exe" http://localhost:8000/file/upload

# Test input length limits
curl -X POST -H "Content-Type: application/json" \
  -d '{"text":"'$(python -c "print('x'*20000)")'"}'  \
  http://localhost:8000/chat
```

#### Rate Limiting Testing

```bash
# Test rate limiting
for i in {1..100}; do
  curl http://localhost:8000/health &
done
```

## Monitoring

### Log Analysis

```bash
# Check security events
grep "SECURITY" /var/log/ai-guardian/app.log

# Monitor authentication failures
grep "AUTH FAILURE" /var/log/ai-guardian/security.log

# Check rate limit violations
grep "Rate limit exceeded" /var/log/ai-guardian/app.log
```

### Performance Monitoring

```bash
# Get current metrics
curl http://localhost:8000/metrics

# Check system health
curl http://localhost:8000/health/detailed
```

## Development Workflow

### Security-First Development

1. **Before coding**: Review security requirements
2. **During development**: 
   - Validate all inputs
   - Use parameterized queries
   - Handle errors securely
   - Log security events
3. **Before commit**: Run security tests
4. **Before deployment**: Run comprehensive tests

### Code Review Checklist

- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Error handling doesn't expose sensitive data
- [ ] Authentication/authorization checks present
- [ ] SQL queries use parameters
- [ ] File operations validate paths
- [ ] Security events logged

### Continuous Security

```bash
# Add to CI/CD pipeline
python test_runner.py security --quiet
python integration_test.py
```

## Troubleshooting

### Common Issues

#### 1. "Rate limit exceeded" errors
- Check rate limiting configuration
- Monitor for unusual traffic patterns
- Adjust limits if needed

#### 2. File upload failures
- Verify file type is allowed
- Check file size limits
- Ensure proper permissions

#### 3. Authentication errors
- Verify JWT configuration
- Check token expiration
- Validate environment variables

### Debug Mode

For debugging (development only):

```env
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

### Security Incident Response

1. **Immediate**: Check logs for security events
2. **Assess**: Determine scope and impact
3. **Contain**: Block suspicious IPs if needed
4. **Investigate**: Analyze attack patterns
5. **Recover**: Restore normal operations
6. **Learn**: Update security measures

## Best Practices

### Input Handling
- Always validate and sanitize input
- Use allowlists instead of blocklists
- Implement proper error handling
- Log suspicious activities

### Authentication
- Use strong, unique secret keys
- Implement proper session management
- Validate tokens on every request
- Log authentication events

### File Operations
- Validate file types and sizes
- Scan for malicious content
- Use secure file storage
- Implement access controls

### Database Security
- Use parameterized queries
- Implement proper access controls
- Encrypt sensitive data
- Regular security updates

## Support

For security questions or to report vulnerabilities:
- Email: security@ai-guardian.com
- Review the [SECURITY.md](SECURITY.md) document
- Check the [GitHub Issues](https://github.com/TranXuanPhong25/ai-guardian/issues)