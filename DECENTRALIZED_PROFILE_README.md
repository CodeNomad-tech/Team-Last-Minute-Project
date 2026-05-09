# 🎓 Decentralized Teacher Profile System

## Overview

The Decentralized Teacher Profile System is a comprehensive digital identity and reputation management system built into the KAFUMBWE Grade Book. It enables teachers to maintain transparent records of their:

- **Professional Information** - Bio, qualifications, and contact details
- **School Fees Payments** - Track all fee payments and obligations
- **Mobile Money Transactions** - Complete financial transaction history
- **Community Endorsements** - Digital reputation built through verified endorsements

## Features

### 1. 👤 Profile Management
Teachers can create and maintain a professional profile that includes:
- Professional biography
- Contact information
- Mobile money account details
- Community reputation score

**Access:** `/profile` or click "👤 My Profile" in navigation

### 2. 💰 School Fees Tracking
Comprehensive fee payment management system that allows teachers to:
- Record all school fee payments
- Track payment status (Pending/Paid)
- Store transaction references
- Generate payment history
- View summary statistics

**Features:**
- Payment amount tracking
- Payment date recording
- Status management (Pending/Paid)
- Transaction reference storage
- Summary dashboard with totals

**Access:** `/profile/fees`

### 3. 📱 Mobile Money History
Maintain a complete financial transaction record including:
- Transfers to other accounts
- Deposits to mobile money
- Withdrawals from mobile money
- Transaction status tracking
- Reference number storage

**Transaction Types:**
- **Transfer:** Money sent to another person/account
- **Deposit:** Money added to your account
- **Withdrawal:** Money taken from your account

**Access:** `/profile/mobile_money`

### 4. 🏆 Community Endorsements
Build digital reputation through community endorsements:
- Receive endorsements from colleagues, students, parents, and community leaders
- 5-star rating system
- Verified and pending endorsement tracking
- Reputation score calculation
- Average rating display

**Endorsement Process:**
1. Teachers can add endorsements from community members
2. Each endorsement includes a message and star rating (1-5)
3. Endorsements are verified by administrators
4. Verified endorsements contribute to reputation score

**Access:** `/profile/endorsements`

## Database Structure

### TeacherProfile Table
```sql
ProfileID (Primary Key)
UserID (Foreign Key - Teachers)
Bio (TEXT)
PhoneNumber (TEXT)
MobileMoneyID (TEXT)
CommunityReputation (INTEGER)
TotalFeesBalance (REAL)
ProfileCreatedDate (DATETIME)
LastUpdated (DATETIME)
```

### FeesPayment Table
```sql
PaymentID (Primary Key)
UserID (Foreign Key - Teachers)
PaymentAmount (REAL)
PaymentDate (DATETIME)
PaymentDescription (TEXT)
PaymentStatus (TEXT: pending/paid)
TransactionReference (TEXT)
```

### MobileMoneyTransaction Table
```sql
TransactionID (Primary Key)
UserID (Foreign Key - Teachers)
TransactionType (TEXT: transfer/deposit/withdrawal)
Amount (REAL)
Recipient (TEXT)
SenderID (TEXT)
TransactionDate (DATETIME)
Status (TEXT: completed/pending/failed)
TransactionReference (TEXT)
Notes (TEXT)
```

### CommunityEndorsement Table
```sql
EndorsementID (Primary Key)
UserID (Foreign Key - Teachers)
EndorserName (TEXT)
EndorsementText (TEXT)
EndorsementScore (INTEGER: 1-5)
EndorsementDate (DATETIME)
Verified (BOOLEAN)
```

## API Routes

### Profile Routes

#### GET /profile
View complete teacher profile with dashboard

#### GET /profile/edit
Edit profile page

#### POST /profile/edit
Update profile information

#### GET /profile/fees
View school fees payment history

#### POST /profile/add_fees
Add new fees payment record

#### GET /profile/mobile_money
View mobile money transaction history

#### POST /profile/add_transaction
Log new mobile money transaction

#### GET /profile/endorsements
View community endorsements

#### POST /profile/add_endorsement
Add new endorsement

## Usage Guide

### Adding a School Fee Payment

1. Navigate to **Fees Management** (`/profile/fees`)
2. Click **"+ Add Payment Record"**
3. Fill in the form:
   - **Amount:** Payment amount in Kwacha
   - **Description:** What the fee is for (e.g., "School Fees - Term 1")
   - **Status:** Pending or Paid
   - **Reference:** Optional transaction reference number
4. Click **"Add Payment"**

### Logging a Mobile Money Transaction

1. Navigate to **Mobile Money History** (`/profile/mobile_money`)
2. Click **"+ Log Transaction"**
3. Select transaction type (Transfer/Deposit/Withdrawal)
4. Enter transaction details:
   - Amount in Kwacha
   - Recipient/Sender information
   - Account ID
   - Transaction reference
5. Add optional notes
6. Click **"Log Transaction"**

### Adding a Community Endorsement

1. Navigate to **Community Endorsements** (`/profile/endorsements`)
2. Click **"+ Add Endorsement"**
3. Enter:
   - **Endorser Name:** Who is endorsing (e.g., "Mr. John Smith", "School Board")
   - **Rating:** 1-5 stars
   - **Message:** Detailed endorsement text
4. Click **"Submit Endorsement"**

## Security & Privacy

- All profile data is stored securely in the database
- Access is restricted to authenticated users
- Users can only view and edit their own profiles
- Endorsements are verified before affecting reputation score
- All transactions are time-stamped for audit purposes

## Reputation System

### How Reputation Score is Calculated

- Based on average rating of all **verified** endorsements
- Scale: 1-5 stars (5.0 = Excellent, 1.0 = Poor)
- Only verified endorsements count toward final score
- Multiple endorsements are averaged

### Reputation Levels
- **4.5-5.0:** Excellent - Highly trusted and respected
- **3.5-4.4:** Very Good - Strong professional standing
- **2.5-3.4:** Good - Reliable and trustworthy
- **1.5-2.4:** Fair - Adequate professional standing
- **Below 1.5:** Poor - Needs improvement

## Benefits

### For Teachers
- Build verifiable professional reputation
- Create transparent financial records
- Support loan/credit applications
- Career advancement documentation
- Community recognition

### For the School
- Transparent teacher financial tracking
- Fee payment monitoring
- Reputation-based staff assessment
- Community trust building
- Audit trail for compliance

### For the Community
- Verified teacher credentials
- Financial reliability indicators
- Community endorsement verification
- Transparent institution management

## Best Practices

1. **Keep Profile Updated:** Regularly update bio and contact information
2. **Record Transactions:** Log all fees and mobile money activities promptly
3. **Honest Endorsements:** Only seek endorsements from genuine interactions
4. **Accurate Information:** Ensure all data entered is correct and complete
5. **Reference Management:** Store all transaction references for verification

## Troubleshooting

### Cannot access profile?
- Ensure you're logged in as a teacher
- Check your user role in the system

### Endorsements not showing?
- Endorsements may be pending verification by administrators
- Check the Verified/Pending status

### Missing transactions?
- Ensure transaction date is correct
- Check if you're viewing the correct time period

## Future Enhancements

- Export profile as PDF certificate
- Integration with blockchain for immutable records
- API for third-party verification
- Advanced analytics and reporting
- Mobile app version
- Multi-language support

## Support & Contact

For technical issues or questions about the Decentralized Profile System, contact:
- System Administrator
- School IT Department

---

**Version:** 1.0  
**Last Updated:** 2026  
**System:** KAFUMBWE Grade Book Platform
