// Get the data from the previous node
const data =  $input.item.json || {};

// Base64 encoded REWE logo (same as before)
const reweLogoBase64 = "https://raw.githubusercontent.com/roo20/n8n/refs/heads/main/rewe_logo_icon_248646.svg";

// Helper for padding strings to align columns
const pad = (str, len) => String(str).padEnd(len, ' ');
const padNum = (num, len) => String(num).padStart(len, ' ');

// --- DYNAMIC CONTENT GENERATION ---

// 1. Create a line for each item in the cart
const itemsHtml = data.items.map(item => {
  const taxCode = item.taxRate === 7 ? 'B' : 'A';
  return `${pad(item.name, 28)}EUR ${padNum(item.price.toFixed(2), 7)} ${taxCode} *`;
}).join('\n');

// 2. Create the tax summary table
let taxTableHtml = 'Steuer %      Netto      Steuer      Brutto\n';
if (data.taxSummary[7].brutto > 0) {
  taxTableHtml += `B=  7,0%     ${padNum(data.taxSummary[7].net, 7)}     ${padNum(data.taxSummary[7].tax, 7)}     ${padNum(data.taxSummary[7].brutto, 7)}\n`;
}
if (data.taxSummary[19].brutto > 0) {
  taxTableHtml += `A= 19,0%     ${padNum(data.taxSummary[19].net, 7)}     ${padNum(data.taxSummary[19].tax, 7)}     ${padNum(data.taxSummary[19].brutto, 7)}\n`;
}

const gesamtNetto = (parseFloat(data.taxSummary[7].net) + parseFloat(data.taxSummary[19].net)).toFixed(2);
const gesamtTax = (parseFloat(data.taxSummary[7].tax) + parseFloat(data.taxSummary[19].tax)).toFixed(2);
taxTableHtml += `Gesamtbetrag  ${padNum(gesamtNetto, 7)}     ${padNum(gesamtTax, 7)}     ${padNum(data.total, 7)}`;

// --- FINAL HTML ---
const html = `
<html>
<head>
  <style>
    body { background-color: #FFF; margin: 0; padding: 0; }
    #receipt { font-family: 'Courier New', Courier, monospace; font-size: 16px; line-height: 1.4; color: #000; background-color: #FFF; padding: 25px; width: 450px; }
    .logo { width: 200px; margin: 0 auto 20px auto; display: block; }
    .center { text-align: center; }
    pre { font-family: 'Courier New', Courier, monospace; font-size: 16px; margin: 0; padding: 0; }
  </style>
</head>
<body>
  <div id="receipt">
    <img class="logo" src="${reweLogoBase64}" alt="REWE Logo" />
    <pre class="center">
REWE
Ballindamm 40
20095 Hamburg
Tel.: 040-27169854
UID Nr.: DE812706034
    </pre>
    <br>
    <pre>
${itemsHtml}
========================================
SUMME                              EUR ${padNum(data.total, 7)}
========================================
Geg. Mastercard                    EUR ${padNum(data.total, 7)}

           * * Kundenbeleg * *

Datum:      ${data.date}
Uhrzeit:    ${data.time1} Uhr
Beleg-Nr.   ${data.belegNr}
Trace-Nr.   ${data.traceNr}

            Bezahlung
            Kontaktlos
            DEBIT MASTERCARD
            ############${data.last4Digits} 0001
Nr.
VU-Nr.                             ${data.vuNr}
Terminal-ID                        ${data.terminalId}
Pos-Info                           00 073 00
AS-Zeit ${data.date.substring(0, 5)}.                       ${data.time1.substring(0, 5)} Uhr
AS-Proc-Code = 00 075 00
Capt.-Ref. = 0000
00 GENEHMIGT
Betrag EUR                         ${padNum(data.total, 7)}

            Zahlung erfolgt

${taxTableHtml}

${data.date}         ${data.time2.substring(0, 5)}      Bon-Nr.:${data.bonNr}
Markt:0112             Kasse:${data.kasseNr}    Bed.:${data.bedNr}
****************************************
Jetzt mit PAYBACK Punkten bezahlen!
Einfach REWE Guthaben am Service-Punkt
                aufladen.

  Für die mit * gekennzeichneten Produkte
   erhalten Sie leider keine Rabatte
           oder PAYBACK Punkte.
****************************************

          REWE Markt GmbH
    Vielen Dank für Ihren Einkauf
Bitte beachten Sie unsere kunden-
freundlichen Öffnungszeiten am Markt

         Sie haben Fragen?
     Antworten gibt es unter
           www.rewe.de
    </pre>
  </div>
</body>
</html>
`;

// Return the HTML for the Browser node
return { json: { html: html } };