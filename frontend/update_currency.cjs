const fs = require("fs");

function processFile(path) {
  let content = fs.readFileSync(path, "utf8");
  let original = content;
  
  // Replace Amount ($) with Amount (₹)
  content = content.replace(/Amount \(\$\)/g, "Amount (₹)");
  
  // Replace $${var} with ₹${var}
  content = content.replace(/\$\$\{/g, "₹${");
  
  if (content !== original) {
    fs.writeFileSync(path, content, "utf8");
    console.log("Updated " + path);
  }
}

["src/pages/CheckTransaction.jsx", "src/pages/Dashboard.jsx", "src/pages/TransactionHistory.jsx", "src/pages/BatchDetection.jsx"].forEach(processFile);
