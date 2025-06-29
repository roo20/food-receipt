// Get input data from previous node
const inputData = $input.item.json || {};
const inputTimestamp = inputData.timestamp ? new Date(inputData.timestamp) : new Date();


// --- CONFIGURATION ---
const possibleItems = [
  { name: 'GURKE', price: 0.79, taxRate: 7 },
  { name: 'BANANEN', price: 1.29, taxRate: 7 },
  { name: 'REWE Bio Apfel', price: 2.49, taxRate: 7 },
  { name: 'Milch 1,5%', price: 1.19, taxRate: 7 },
  { name: 'Butter', price: 2.29, taxRate: 7 },
  { name: 'PRESSEERZEUGNIS', price: 2.00, taxRate: 7 },
  { name: 'Joghurt', price: 0.59, taxRate: 7 },
  { name: 'Vollkornbrot', price: 1.89, taxRate: 19 },
  { name: 'Salami', price: 1.99, taxRate: 19 },
  { name: 'Käse', price: 2.99, taxRate: 19 },
  { name: 'Energy Drink', price: 1.49, taxRate: 19 },
  { name: 'Kaffee Crema', price: 0.99, taxRate: 7 },
  { name: 'Wasser', price: 5.99, taxRate: 19 },
];

// --- LOGIC ---
// 1. Create a shopping cart and add items until total is over 7
const shoppingCart = [];
let currentTotal = 0;
while (currentTotal < 7) {
  const randomItem = possibleItems[Math.floor(Math.random() * possibleItems.length)];
  shoppingCart.push(randomItem);
  currentTotal += randomItem.price;
}

// 2. Calculate tax breakdown
const taxSummary = {
  7: { net: 0, tax: 0, brutto: 0 },
  19: { net: 0, tax: 0, brutto: 0 }
};

for (const item of shoppingCart) {
  const rate = item.taxRate;
  const brutto = item.price;
  const net = brutto / (1 + rate / 100);
  const tax = brutto - net;
  
  taxSummary[rate].net += net;
  taxSummary[rate].tax += tax;
  taxSummary[rate].brutto += brutto;
}

// 3. Helper function for random numbers
const getRandomNum = (length) => Math.floor(Math.random() * (10 ** length));

// 4. Generate random times between 8 AM and 6 PM
const receiptTime = new Date(inputTimestamp);
// Set random hour between 8 (8 AM) and 17 (5 PM) - so latest is 5:59 PM
receiptTime.setHours(8 + Math.floor(Math.random() * 10)); // 8-17 hours
receiptTime.setMinutes(Math.floor(Math.random() * 60)); // 0-59 minutes
receiptTime.setSeconds(Math.floor(Math.random() * 60)); // 0-59 seconds

// Generate transaction time (3-5 minutes before receipt time for processing)
const transactionTime = new Date(receiptTime.getTime() - (3 + Math.floor(Math.random() * 3)) * 60000);

// 5. Generate all dynamic data
const data = {
  // Item & Total Data
  items: shoppingCart,
  total: currentTotal.toFixed(2),
  taxSummary: {
      7: {
          net: taxSummary[7].net.toFixed(2),
          tax: taxSummary[7].tax.toFixed(2),
          brutto: taxSummary[7].brutto.toFixed(2),
      },
      19: {
          net: taxSummary[19].net.toFixed(2),
          tax: taxSummary[19].tax.toFixed(2),
          brutto: taxSummary[19].brutto.toFixed(2),
      }
  },
  
  // Dates and Times (using input timestamp as base)
  date: receiptTime.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }),
  time1: transactionTime.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }), // Transaction time
  time2: receiptTime.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }), // Receipt print time
  
  // Random IDs
  belegNr: String(getRandomNum(4)).padStart(4, '0'),
  traceNr: String(getRandomNum(6)).padStart(6, '0'),
  bonNr: String(getRandomNum(4) + 5000),
  bedNr: String(getRandomNum(6)).padStart(6, '0'),
  kasseNr: String(getRandomNum(2) + 1),
  vuNr: String(getRandomNum(9)).padStart(9, '0'),
  terminalId: String(getRandomNum(8)).padStart(8, '0'),
  last4Digits: String(getRandomNum(4)).padStart(4, '0'),
  
  // Additional metadata
  originalTimestamp: inputData.timestamp,
  timezone: inputData.Timezone,
  dayOfWeek: receiptTime.toLocaleDateString('de-DE', { weekday: 'long' }),
  monthYear: receiptTime.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' })
};

// Return the data for the next node
return {json: data };