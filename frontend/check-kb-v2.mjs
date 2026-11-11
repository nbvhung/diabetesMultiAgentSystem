// Actual authenticated demo and Neo4j UI smoke check; no mocked graph data.
import {chromium} from '@playwright/test';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const match=readFileSync(path.join(root,'.env.demo'),'utf8').match(/^DEMO_ACCESS_PASSWORD=(.*)$/m);
if(!match)throw new Error('Demo credentials missing');
const password=match[1].trim().replace(/^(['"])(.*)\1$/,'$2');
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const out=path.join(root,'docs/validation/report_v2');mkdirSync(out,{recursive:true});
try{
 const context=await browser.newContext({httpCredentials:{username:'demo',password},viewport:{width:1440,height:1000}});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8082');
 await page.getByRole('navigation').getByRole('button',{name:/Đồ thị tri thức/}).click();
 await page.getByRole('heading',{name:'Đồ thị tri thức diabetes'}).waitFor();
 await page.getByRole('heading',{name:'diabetes → HAS_SYMPTOM → thirst'}).waitFor({timeout:90000});
 const count=await page.locator('.topic-list article').count();if(count!==11)throw new Error('Unexpected assertion count');
 await page.getByRole('textbox',{name:'Lọc khái niệm hoặc quan hệ'}).fill('HAS_SYMPTOM');
 if(await page.locator('.topic-list article').count()!==3)throw new Error('Filter failed');
 await page.locator('article summary').first().click();
 await page.screenshot({path:path.join(out,'kb-desktop.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 if(!await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth))throw new Error('Mobile overflow');
 await page.screenshot({path:path.join(out,'kb-mobile.png'),fullPage:true});
 if(errors.length)throw new Error('Browser errors');
 const result={status:'PASS',assertions:count,filtered_symptoms:3,mobile_overflow:false,browser_errors:errors,data:'Actual demo API and Neo4j'};
 writeFileSync(path.join(out,'browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{await browser.close();}
