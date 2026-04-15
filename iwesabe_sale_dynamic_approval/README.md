# 🔄 Sales Order Dynamic Approval

> Multi-level approval workflow for Odoo 17 Sale Orders

## 🎯 Features
- 🔐 Role-based approval steps per Sales Team
- 🔔 Auto-notification to next approver (bell + email)
- 📊 Visual status badge: "Pending Approval: [User]"
- 🔄 Auto-sync approvers from Team → Quotation
- 📝 Full audit trail in SO chatter

## 📋 Configuration Guide
See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for detailed setup instructions.

## 🚀 Quick Start
1. Install module via Apps menu or command line
2. Configure approvers: Sales → Configuration → Sales Teams → [Team] → "Sale Order Approver(s)"
3. Create quotation with configured team → workflow activates automatically

## 👥 User Workflow
```mermaid
graph LR
    A[Sales: Create Quotation] --> B[Click Confirm]
    B --> C{Is user first approver?}
    C -->|Yes| D[Mark approved + Notify next]
    C -->|No| E[Error: Not authorized]
    D --> F[Manager receives 🔔 notification]
    F --> G[Manager reviews → Approve/Cancel]
    G -->|Approve| H[Order confirmed → Warehouse]