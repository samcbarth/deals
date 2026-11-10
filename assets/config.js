/*
 * Site-wide network ids. One place to paste account values.
 * Empty value = the matching slot renders nothing (no blank boxes, no placeholder ads).
 *
 * AMAZON_TAG      Amazon Associates tracking id, e.g. "samdeals-20". Also read by build.py,
 *                 which bakes it into every "Check price on Amazon" link. Re-run build after editing.
 * ADSENSE_CLIENT  AdSense publisher id, e.g. "ca-pub-1234567890123456".
 * HUBSPOT_PORTAL  HubSpot portal for the contact form (Sam's portal is 20693956).
 * HUBSPOT_FORM_ID HubSpot form GUID. Empty = contact page shows the email fallback instead.
 * CONTACT_EMAIL   Fallback contact address shown when no form id is set.
 */
window.SITE_CONFIG = {
  AMAZON_TAG: '',
  ADSENSE_CLIENT: '',
  HUBSPOT_PORTAL: '20693956',
  HUBSPOT_FORM_ID: '',
  CONTACT_EMAIL: ''
};
