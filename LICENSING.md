# Fleet MCP Licensing

Fleet MCP uses a **dual-use licensing model** that allows free use for development and testing, while requiring a commercial license for production deployments.

## Quick Summary

| Use Case | License Required | Cost |
|----------|------------------|------|
| Local development | ❌ No | Free |
| Testing & evaluation | ❌ No | Free |
| Commercial testing (14 days max) | ❌ No | Free |
| Production deployment | ✅ Yes | Commercial |
| Commercial services | ✅ Yes | Commercial |

## When a License is NOT Required (Free Use)

You can use Fleet MCP **without a license** for:

### Development & Testing
- **Local Development**: Running Fleet MCP on your personal computer or development machine
- **Internal Testing**: Testing within your organization before production deployment
- **Proof of Concept**: Evaluating Fleet MCP for potential use
- **Learning**: Educational purposes and learning how to use the tool
- **Commercial Testing (Limited)**: Testing in a commercial setting for up to 14 days for evaluation purposes

### Evaluation Environments
- **Staging/Pre-Production**: Testing in staging environments that mirror production but are not live
- **Lab Environments**: Isolated testing environments
- **Demo Environments**: Internal demonstrations to stakeholders

### Specific Scenarios (No License Needed)
- Running on `localhost` or `127.0.0.1`
- Running on private/internal networks for testing
- Running in development containers or VMs
- Running in CI/CD pipelines for testing purposes
- Running in educational institutions for teaching

## When a License IS Required (Commercial Use)

You **must obtain a commercial license** for:

### Production Deployments
- **Live Production**: Any deployment managing real systems in production
- **Managed Services**: Offering Fleet MCP as a service to customers
- **SaaS Deployments**: Hosting Fleet MCP for external users
- **Commercial Products**: Including Fleet MCP in commercial offerings

### Commercial Use Cases
- **Revenue-Generating**: Any use where Fleet MCP is part of a revenue-generating activity
- **Customer-Facing**: Deployments accessible to external customers
- **Enterprise Deployments**: Using Fleet MCP to manage enterprise infrastructure for commercial purposes
- **Resale/Redistribution**: Bundling or reselling Fleet MCP as part of a commercial product

### Specific Scenarios (License Required)
- Deploying to production servers
- Hosting on public/internet-accessible domains
- Using in commercial managed services
- Offering as part of a paid service
- Deploying in customer environments
- Using in revenue-generating applications
- Commercial testing beyond 14 days

## Examples

### ✅ No License Required

```
1. Developer testing Fleet MCP locally
   - Running on localhost:8000
   - Testing against a local Fleet instance
   - Result: FREE - No license needed

2. Company evaluating Fleet MCP
   - Testing in internal staging environment
   - Accessible only to internal network
   - Not yet in production
   - Result: FREE - No license needed

3. Educational institution
   - Teaching students about Fleet DM
   - Running in lab environment
   - Non-commercial use
   - Result: FREE - No license needed

4. Internal IT team
   - Testing Fleet MCP before production rollout
   - Running in isolated test environment
   - Not yet managing live systems
   - Result: FREE - No license needed

5. Company evaluating for commercial use
   - Testing in commercial environment for 10 days
   - Evaluating before production deployment
   - Within 14-day evaluation window
   - Result: FREE - No license needed
```

### ✅ License Required

```
1. Company deploying to production
   - Fleet MCP managing live production systems
   - Deployed to production servers
   - Managing real device fleet
   - Result: COMMERCIAL LICENSE REQUIRED

2. Managed service provider
   - Offering Fleet MCP as a managed service
   - Hosting for multiple customers
   - Customers pay for the service
   - Result: COMMERCIAL LICENSE REQUIRED

3. SaaS company
   - Including Fleet MCP in SaaS offering
   - Customers access via web interface
   - Revenue-generating service
   - Result: COMMERCIAL LICENSE REQUIRED

4. Enterprise software vendor
   - Bundling Fleet MCP in commercial product
   - Selling to enterprise customers
   - Part of commercial offering
   - Result: COMMERCIAL LICENSE REQUIRED

5. Company testing beyond evaluation period
   - Testing in commercial environment for 30 days
   - Exceeds 14-day evaluation window
   - Result: COMMERCIAL LICENSE REQUIRED
```

## Obtaining a Commercial License

### Contact Information

For commercial licensing inquiries, please contact:

<!-- - **Email**: <TODO: Add email> -->
- **GitHub Issues**: https://github.com/SimplyMinimal/fleet-mcp/issues

### License Application Process

1. **Contact**: Reach out with your use case and deployment details
2. **Evaluation**: We'll review your requirements
3. **Agreement**: Discuss commercial license terms
4. **Activation**: Receive your license key and activation details

### What's Included in Commercial License

- Right to use Fleet MCP in production environments
- Commercial support and updates
- License key for deployment
- Commercial license agreement
- Priority bug fixes and feature requests

## Frequently Asked Questions

### Q: I'm running Fleet MCP on a private network. Do I need a license?

**A:** If it's for internal testing and evaluation purposes, no license is required. However, if you're using it in production to manage live systems, a commercial license is required regardless of network accessibility.

### Q: Can I use Fleet MCP in a Docker container without a license?

**A:** Yes, if it's for development, testing, or evaluation. If you're deploying the container to production to manage live systems, a commercial license is required.

### Q: What if I'm using Fleet MCP internally but not generating revenue?

**A:** If you're using it for internal operations (not as a service to others), it depends on whether it's production or testing:
- **Testing/Evaluation**: No license needed
- **Production (managing live systems)**: Commercial license required

### Q: Can I modify Fleet MCP for my own use without a license?

**A:** Yes, you can modify Fleet MCP for development and testing purposes without a license. For production use of modified versions, a commercial license is still required.

### Q: Do I need a license for CI/CD pipeline testing?

**A:** No, using Fleet MCP in CI/CD pipelines for testing purposes does not require a license. This is considered testing use.

### Q: What about using Fleet MCP in a staging environment?

**A:** Staging environments used for testing before production do not require a license. However, once you move to production, a commercial license is required.

### Q: Can I use Fleet MCP for a free/open-source project?

**A:** If your project is non-commercial and for internal use only, no license is required. If you're offering it as a service to others (even for free), a commercial license is required.

### Q: What happens if I use Fleet MCP in production without a license?

**A:** Using Fleet MCP in production without a required commercial license violates the licensing terms. We encourage you to contact us for licensing information. Future versions may include license validation.

### Q: How long can I test Fleet MCP in a commercial setting?

**A:** You can test Fleet MCP in a commercial setting for up to 14 days without a license. After 14 days, a commercial license is required.

### Q: Is there a trial commercial license?

**A:** Yes, we offer trial licenses for evaluation purposes. Contact us to discuss trial options.

## License Compliance

### For Users

- Ensure you understand whether your use case requires a license
- Obtain a commercial license before deploying to production
- Keep your license key secure and confidential
- Review the commercial license agreement for specific terms

### For Developers

- Respect the licensing terms when using Fleet MCP
- Do not circumvent license validation mechanisms
- Report licensing questions or concerns to the team
- Contribute improvements back to the project

## Support

For licensing questions or to discuss your specific use case:

1. **Check this document**: Review the examples and FAQ
2. **Contact us**: Reach out with your specific scenario
3. **GitHub Issues**: Open an issue for licensing discussions
<!-- 4. **Email**: Send detailed questions to <TODO: Add email> -->

## Changes to Licensing

This licensing model may be updated in future versions. We will provide notice of significant changes. Existing commercial licenses will be honored according to their terms.

---

**Last Updated**: 2025-10-20
**Version**: 1.0

