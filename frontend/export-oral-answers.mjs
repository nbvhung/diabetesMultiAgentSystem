import {chromium} from '@playwright/test';
import {fileURLToPath,pathToFileURL} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const base=path.join(root,'docs/defense/tra_loi_51_cau_van_dap');
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const page=await browser.newPage();
 await page.goto(pathToFileURL(base+'.html').href);
 await page.pdf({path:base+'.pdf',format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,headerTemplate:'<span></span>',footerTemplate:'<div style="font-size:9px;width:100%;text-align:center;color:#666">B23DCCN358 · Ôn tập vấn đáp · <span class="pageNumber"></span>/<span class="totalPages"></span></div>'});
 console.log('PDF exported; answer headings: '+await page.locator('h3').count());
}finally{await browser.close();}
