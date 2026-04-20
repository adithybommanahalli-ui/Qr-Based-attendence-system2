// QR scanner utilities — html5-qrcode is loaded via CDN in base.html
// This file is a placeholder for any additional QR helper functions

function stopQRScanner(scanner) {
  if (scanner) {
    scanner.stop().catch(() => {});
  }
}
