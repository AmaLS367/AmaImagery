# Troubleshooting Documentation

## Overview

Common issues, solutions, and debugging guides for the AI Image Generator.

## Quick Links

- [Common Issues](./common-issues.md) - Frequently encountered problems
- [Error Codes](./error-codes.md) - Error code reference
- [GPU Issues](./gpu-issues.md) - GPU-related problems
- [Memory Issues](./memory-issues.md) - Out of memory errors
- [Performance Issues](./performance-issues.md) - Performance optimization

## Common Issues

### Installation Problems

#### Issue: CUDA not found
**Symptoms:** `RuntimeError: CUDA not available`
**Solution:**
1. Verify NVIDIA drivers installed
2. Install CUDA toolkit 11.8+
3. Reinstall PyTorch with CUDA support
```bash
pip install torch==2.2.2+cu121 --index-url https://download.pytorch.org/whl/cu121
```

#### Issue: Out of VRAM
**Symptoms:** `CUDA out of memory`
**Solutions:**
1. Reduce image resolution
2. Lower `CUDA_VRAM_FRACTION` in settings
3. Enable model offloading
4. Close other GPU applications

### Runtime Errors

#### Issue: Model loading fails
**Symptoms:** Model files not found or corrupted
**Solutions:**
1. Verify model files in `models/` directory
2. Re-download models
3. Check file permissions
4. Verify disk space

#### Issue: Slow generation
**Symptoms:** Generation takes too long
**Solutions:**
1. Check GPU utilization
2. Enable xformers
3. Reduce inference steps
4. Verify no CPU fallback

### Database Issues

#### Issue: Migration failures
**Symptoms:** Alembic migration errors
**Solutions:**
1. Check database connection
2. Verify PostgreSQL is running
3. Check migration history
```bash
alembic current
alembic history
```

#### Issue: Connection pool exhausted
**Symptoms:** `QueuePool limit exceeded`
**Solutions:**
1. Increase pool size in settings
2. Check for connection leaks
3. Restart database

### Docker Issues

#### Issue: Container won't start
**Symptoms:** Container exits immediately
**Solutions:**
1. Check logs: `docker logs <container>`
2. Verify environment variables
3. Check port conflicts
4. Verify volume mounts

## Getting Help

1. Check this documentation
2. Search existing issues
3. Enable debug logging
4. Collect error messages and logs
5. Report issues with:
   - Error message
   - Steps to reproduce
   - Environment details
   - Relevant logs

## Debug Mode

Enable debug logging:
```bash
# .env
DEBUG=1
LOG_LEVEL=DEBUG
```

View logs:
```bash
# Application logs
tail -f logs/app/*.log

# Error logs
tail -f logs/errors/*.log
```

## System Information

Collect system info for bug reports:
```bash
# GPU info
nvidia-smi

# Python packages
pip list

# Docker info
docker --version
docker compose version

# System info
uname -a
```

