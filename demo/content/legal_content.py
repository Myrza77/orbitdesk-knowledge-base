# -*- coding: utf-8 -*-
"""
legal_content.py

Hand-written knowledge-base article content for all 29 categories, split
into two honest kinds of "Law" status:

  source='external' -- backed by real, verified international law/regulation.
    Citations checked against primary/reputable sources before writing,
    not recalled from memory. Where a category's real-world equivalent
    genuinely has no regulatory content (e.g. password recovery), it is
    NOT force-fit into this bucket.

  source='internal' -- OrbitDesk's own invented internal policy, written
    for a fictional company, for demo completeness. Not a real law,
    not attributed to any real regulation, clearly labeled as such in
    the UI (see build_kb_demo.py).

Verified external sources used:
  - Directive 2011/83/EU (EU Consumer Rights Directive), Art. 9-16 (right
    of withdrawal / refund), Art. 18 (30-day default delivery)
  - GDPR (EU) 2016/679, Art. 15 (access), Art. 16 (rectification),
    Art. 17 (erasure), Art. 21(2) (right to object to marketing)
  - PSD2 (EU) 2015/2366, Strong Customer Authentication requirement
  - ePrivacy Directive 2002/58/EC, Art. 13 (marketing consent/opt-out)
"""

ARTICLES = {

    # ============ ACCOUNT ============
    'create_account': {
        'title': 'Create account',
        'body': 'New accounts require a valid email address and confirmation via a one-time verification link, per OrbitDesk\'s standard onboarding flow. No purchase or payment method is required to create an account. Duplicate accounts under the same verified email are merged automatically, not created as separate records.',
        'source': 'internal',
        'legal_statement': 'Account creation follows OrbitDesk\'s internal identity-verification standard (email confirmation required before first order).',
    },
    'delete_account': {
        'title': 'Delete account',
        'body': 'Customers may request full account deletion at any time. Under GDPR Article 17 (right to erasure), OrbitDesk must erase the customer\'s personal data without undue delay once a valid request is received, unless retention is required for an active legal obligation (e.g. unresolved payment dispute, tax record retention period). Order history tied to unresolved disputes is anonymized rather than deleted until the dispute closes.',
        'source': 'external',
        'legal_statement': 'Deletion requests are handled under GDPR Article 17 (right to erasure) -- data is erased without undue delay unless a legal retention obligation applies.',
    },
    'edit_account': {
        'title': 'Edit account details',
        'body': 'Customers can correct inaccurate personal data (name, address, contact details) via account settings at any time. Under GDPR Article 16 (right to rectification), OrbitDesk must action a rectification request without undue delay, and must notify any third party the data was previously shared with, unless that proves impossible or disproportionately difficult.',
        'source': 'external',
        'legal_statement': 'Rectification requests are handled under GDPR Article 16 -- corrections are actioned without undue delay.',
    },
    'recover_password': {
        'title': 'Recover password',
        'body': 'Password recovery requires verification via the email address or phone number on file. A time-limited reset link is sent; it expires after 30 minutes for security. Agents can never reset a password directly on a customer\'s behalf over chat -- this prevents social-engineering account takeover, per OrbitDesk\'s account security standard.',
        'source': 'internal',
        'legal_statement': 'Password recovery follows OrbitDesk\'s internal account-security standard (agent-assisted resets are never performed directly).',
    },
    'registration_problems': {
        'title': 'Registration problems',
        'body': 'Common registration failures: email already registered (direct the customer to password recovery instead), verification email not received (check spam folder, resend after 2 minutes), phone verification code expired (codes are valid for 10 minutes, can be resent). Escalate to technical support if none of the above resolves it within one exchange.',
        'source': 'internal',
        'legal_statement': 'Registration troubleshooting follows OrbitDesk\'s internal support playbook, not an external regulation.',
    },
    'switch_account': {
        'title': 'Switch / upgrade account tier',
        'body': 'Account tier changes (e.g. standard to premium) take effect immediately upon confirmation and are prorated for the current billing period. Downgrades take effect at the start of the next billing cycle, not immediately, so the customer keeps the benefits they already paid for.',
        'source': 'internal',
        'legal_statement': 'Tier-switch timing follows OrbitDesk\'s internal billing policy.',
    },

    # ============ CANCEL ============
    'check_cancellation_fee': {
        'title': 'Check cancellation fee',
        'body': 'For distance sales to EU consumers, Directive 2011/83/EU gives a 14-day right of withdrawal with no cancellation fee or justification required -- the customer only bears the direct cost of returning goods, and only if OrbitDesk clearly disclosed that cost before purchase. Outside that 14-day window, or for the excluded categories listed in Article 16 (custom/personalized goods, perishables, unsealed hygiene items), a cancellation fee may apply per OrbitDesk\'s standard terms.',
        'source': 'external',
        'legal_statement': 'Within the 14-day withdrawal period (Directive 2011/83/EU, Art. 9-16), no cancellation fee applies beyond disclosed return shipping cost.',
    },

    # ============ CONTACT ============
    'contact_customer_service': {
        'title': 'Contact customer service',
        'body': 'Standard support channels are live chat and email, both available during posted support hours. Live chat targets a first response within 5 minutes during business hours; email targets a response within 24 hours. Neither channel guarantees resolution time -- only first response.',
        'source': 'internal',
        'legal_statement': 'Response-time targets are OrbitDesk\'s internal service standard, not a statutory requirement.',
    },
    'contact_human_agent': {
        'title': 'Escalate to a human agent',
        'body': 'Any customer who explicitly asks for a human agent, or whose issue the assistant fails to resolve after two exchanges, is escalated immediately -- no forced additional bot interaction. Escalated conversations keep full context (prior messages, order history) so the customer never has to repeat themselves.',
        'source': 'internal',
        'legal_statement': 'Escalation trigger and context-handoff rule are OrbitDesk\'s internal support standard.',
    },

    # ============ DELIVERY ============
    'delivery_options': {
        'title': 'Delivery options',
        'body': 'Standard delivery (5-7 business days) is included at no extra cost above the order threshold shown at checkout. Express delivery (1-2 business days) is available at checkout for an additional fee, subject to destination and item availability. Delivery option cannot be changed after an order has shipped.',
        'source': 'internal',
        'legal_statement': 'Which delivery tiers are offered, and their pricing, is a commercial choice, not a regulated matter.',
    },
    'delivery_period': {
        'title': 'Delivery period',
        'body': 'Unless a specific delivery date was agreed at checkout, Directive 2011/83/EU Article 18 requires delivery within 30 days of the order being placed. If that deadline is missed, the customer must be given a reasonable additional period to receive the goods; if delivery still fails, the customer is entitled to cancel the order and receive a full refund without further delay.',
        'source': 'external',
        'legal_statement': 'Default delivery deadline and the customer\'s remedy if missed are set by Directive 2011/83/EU, Article 18.',
    },

    # ============ FEEDBACK ============
    'complaint': {
        'title': 'File a formal complaint',
        'body': 'Formal complaints are logged with a reference number and acknowledged within 24 hours. Complaints about a specific order are linked to that order\'s record. Agents summarize the complaint back to the customer before closing the interaction, to confirm nothing was missed -- this is OrbitDesk\'s own escalation-quality standard, not a legal requirement.',
        'source': 'internal',
        'legal_statement': 'Complaint intake and acknowledgment timing follow OrbitDesk\'s internal service standard.',
    },
    'review': {
        'title': 'Leave / manage a product review',
        'body': 'Reviews can only be left by customers with a verified completed purchase of that item. Reviews are moderated for spam and abusive language, not for negative sentiment -- a genuine negative review about product quality or delivery is never removed for being negative.',
        'source': 'internal',
        'legal_statement': 'Review eligibility and moderation policy are set internally by OrbitDesk, not by external regulation.',
    },

    # ============ INVOICE ============
    'check_invoice': {
        'title': 'Check invoice',
        'body': 'Invoices are available in the customer\'s account under Order History within 24 hours of shipment, and are also emailed automatically at that time. Agents can resend an invoice to the email on file but cannot redirect an invoice to a different email without identity verification, to prevent billing-fraud attempts.',
        'source': 'internal',
        'legal_statement': 'Invoice delivery timing and the identity-verification-before-redirect rule are OrbitDesk\'s internal billing-security policy.',
    },
    'get_invoice': {
        'title': 'Get a copy of an invoice',
        'body': 'Customers can request a reissued copy of any invoice from the last 24 months directly from Order History. Older invoices are archived and require a support request, which is fulfilled within 2 business days. There is no fee for reissuing an invoice.',
        'source': 'internal',
        'legal_statement': 'Invoice retention window and reissue turnaround are OrbitDesk\'s internal record-keeping policy.',
    },

    # ============ ORDER ============
    'cancel_order': {
        'title': 'Cancel an order',
        'body': 'Orders not yet shipped can be cancelled instantly with a full refund, no fee. Once shipped, cancellation converts to a return request instead -- covered by the 14-day withdrawal right under Directive 2011/83/EU Art. 9-16, which still applies with no cancellation fee beyond disclosed return shipping.',
        'source': 'external',
        'legal_statement': 'Post-shipment cancellation is treated as withdrawal under Directive 2011/83/EU, Art. 9-16 -- no fee beyond disclosed return cost.',
    },
    'change_order': {
        'title': 'Change an order',
        'body': 'Order contents (items, quantities, shipping address) can be changed only before the order enters the fulfillment queue, typically within 30 minutes of placing it. After that, the change is handled as a cancellation of the original order plus a new order, so the customer is not double-charged.',
        'source': 'internal',
        'legal_statement': 'The 30-minute edit window before fulfillment is OrbitDesk\'s internal operations policy.',
    },
    'place_order': {
        'title': 'Place an order',
        'body': 'Orders can be placed as a guest or as a registered account; guest orders can be claimed into an account later using the order confirmation email. Payment is authorized at checkout and captured only once the order enters fulfillment, so a cancelled-before-fulfillment order is never actually charged.',
        'source': 'internal',
        'legal_statement': 'Guest-checkout support and the authorize-then-capture payment flow are OrbitDesk\'s internal checkout design.',
    },
    'track_order': {
        'title': 'Track an order',
        'body': 'Tracking becomes available once the order leaves the warehouse, usually within 1 business day of the order being placed. Tracking status updates lag the carrier\'s own system by up to a few hours -- if a customer\'s tracking looks stuck, the underlying carrier status is the source of truth, not OrbitDesk\'s cached copy.',
        'source': 'internal',
        'legal_statement': 'Tracking availability timing is an operational fact, not a regulated matter.',
    },

    # ============ PAYMENT ============
    'check_payment_methods': {
        'title': 'Check accepted payment methods',
        'body': 'OrbitDesk accepts major debit/credit cards, and regional wallets where locally available. All card payments from EU/EEA customers require Strong Customer Authentication (SCA) under PSD2 -- typically a second factor via the customer\'s bank app or an SMS code. Payments under EUR 30 may be exempted from SCA at the issuing bank\'s discretion, not OrbitDesk\'s.',
        'source': 'external',
        'legal_statement': 'Card payments from EU/EEA customers require Strong Customer Authentication under PSD2 (Directive (EU) 2015/2366).',
    },
    'payment_issue': {
        'title': 'Report a payment issue',
        'body': 'A declined payment is usually the issuing bank rejecting Strong Customer Authentication (PSD2), an expired card, or insufficient funds -- OrbitDesk cannot see the specific bank-side reason, only that the charge was declined. Agents should direct the customer to retry with the bank\'s authentication app open, or to contact their bank directly for the decline reason.',
        'source': 'external',
        'legal_statement': 'Most EU payment declines trace back to PSD2 Strong Customer Authentication failing on the bank side, not to OrbitDesk\'s checkout.',
    },

    # ============ REFUND ============
    'check_refund_policy': {
        'title': 'Check refund policy',
        'body': 'For EU consumers, the statutory right of withdrawal (Directive 2011/83/EU, Art. 9-16) gives 14 days from delivery to return most items for a full refund, no reason required. Excluded: custom/personalized items, perishables, and unsealed hygiene products (Art. 16 exceptions). Outside the EU/EEA, OrbitDesk\'s own 30-day goodwill return policy applies instead.',
        'source': 'external',
        'legal_statement': 'EU refund eligibility and exceptions are set by Directive 2011/83/EU, Articles 9-16.',
    },
    'get_refund': {
        'title': 'Process a refund',
        'body': 'Once a valid withdrawal or return is confirmed, Directive 2011/83/EU Article 13 requires the refund to use the same payment method the customer originally used, and to be issued without undue delay -- no later than 14 days after OrbitDesk is notified, though OrbitDesk may withhold the refund until the goods are received back or proof of return is provided.',
        'source': 'external',
        'legal_statement': 'Refund method and 14-day maximum timing are set by Directive 2011/83/EU, Article 13.',
    },
    'track_refund': {
        'title': 'Track a refund',
        'body': 'Refunds appear on the customer\'s original payment method within 3-5 business days after OrbitDesk issues them, though the exact posting time depends on the customer\'s bank, not OrbitDesk. If more than 14 days have passed since OrbitDesk confirmed the refund was issued, escalate -- that exceeds the Article 13 maximum and needs investigation, not just reassurance.',
        'source': 'external',
        'legal_statement': 'The 14-day refund-issuance ceiling referenced here is set by Directive 2011/83/EU, Article 13; bank posting time beyond that is outside OrbitDesk\'s control.',
    },

    # ============ SHIPPING ============
    'change_shipping_address': {
        'title': 'Change shipping address',
        'body': 'Shipping address can be changed only before the order ships. Once shipped, OrbitDesk can request a redirect with the carrier on the customer\'s behalf, but success is not guaranteed and depends on the carrier\'s own policy -- this is communicated to the customer as a best-effort request, not a promise.',
        'source': 'internal',
        'legal_statement': 'The pre-shipment cutoff for address changes is OrbitDesk\'s internal fulfillment policy.',
    },
    'set_up_shipping_address': {
        'title': 'Set up a shipping address',
        'body': 'Customers can save multiple shipping addresses and choose a default at checkout. Address validation runs automatically against carrier-recognized formats; an address that fails validation is flagged for manual confirmation before the order can be placed, to reduce failed-delivery rates.',
        'source': 'internal',
        'legal_statement': 'Address validation is OrbitDesk\'s internal delivery-quality measure.',
    },

    # ============ SUBSCRIPTION ============
    'newsletter_subscription': {
        'title': 'Newsletter subscription / unsubscribe',
        'body': 'Marketing emails require prior opt-in consent under the ePrivacy Directive Article 13, except for existing customers being informed about similar products (the "soft opt-in" exception). Unsubscribing must be at least as easy as subscribing was -- one click, no login required -- per GDPR Article 21(2), and takes effect immediately, not at the end of a billing or campaign cycle.',
        'source': 'external',
        'legal_statement': 'Marketing consent and one-click unsubscribe are required by ePrivacy Directive Art. 13 and GDPR Art. 21(2).',
    },

    # ============ Promoted from the uncategorized backlog ============
    'support_hours_inquiry': {
        'title': 'Support hours inquiry',
        'body': 'Live chat and phone support operate Monday-Friday, 09:00-18:00 in the customer\'s local time zone where available, otherwise UTC. Email support is monitored outside those hours but only actioned during business hours. This is an operational schedule, not a regulated service-level obligation.',
        'source': 'internal',
        'legal_statement': 'Support hours are OrbitDesk\'s internal staffing schedule.',
    },
    'formal_complaint_filing': {
        'title': 'Formal complaint filing procedure',
        'body': 'A "formal" complaint (as distinct from routine feedback) is logged with a case number, assigned an owner, and the customer receives written acknowledgment within 24 hours and a substantive response within 5 business days. If unresolved after that, the customer is informed of their right to escalate to their national consumer protection authority for EU purchases.',
        'source': 'internal',
        'legal_statement': 'Internal escalation SLA; the reference to a national consumer authority reflects a general EU consumer right, not a specific cited regulation for this workflow.',
    },
}

assert len(ARTICLES) == 29, f"expected 29 categories, got {len(ARTICLES)}"
print(f"Loaded {len(ARTICLES)} hand-written articles: "
      f"{sum(1 for a in ARTICLES.values() if a['source']=='external')} external, "
      f"{sum(1 for a in ARTICLES.values() if a['source']=='internal')} internal")
