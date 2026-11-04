const {chromium}=require('../frontend/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url'),{execFileSync}=require('child_process');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'docs/report');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.PHASE07_CHROMIUM_PATH||undefined,headless:true});
 try{
  const page=await browser.newPage();await page.goto(pathToFileURL(path.join(folder,'report_print.html')).href,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
  const images=await page.locator('main img').evaluateAll(images=>images.map(img=>({src:img.getAttribute('src'),ok:img.complete&&img.naturalWidth>0})));
  if(images.some(img=>!img.ok))throw Error('A report figure failed to load');
  const headings=await page.evaluate(()=>{
   const headings=[...document.querySelectorAll('main h1,main h2')].map((node,index)=>{node.id='report-h-'+index;return {id:node.id,title:node.textContent,level:Number(node.tagName[1])};});
   document.querySelector('#toc').innerHTML=headings.map(h=>`<div class="toc-entry level-${h.level}"><a href="#${h.id}">${h.title}</a><span class="toc-number" data-id="${h.id}">000</span></div>`).join('');
   document.querySelector('#figures').innerHTML=[...document.querySelectorAll('main figcaption')].map(node=>`<p>${node.textContent}</p>`).join('');
   return headings;
  });
  fs.writeFileSync(path.join(folder,'pdf_headings.json'),JSON.stringify(headings,null,2));
  const pdf=path.join(folder,'tieuluan_final_06_13_hungnbv.pdf');
  const options={path:pdf,format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,headerTemplate:'<div style="font:8px Times New Roman;width:100%;text-align:right;margin:0 23mm;color:#555">DIABETES MULTI-AGENT INTELLIGENT SUPPORT SYSTEM | NHÓM 13 – LỚP 06</div>',footerTemplate:'<div style="font:9px Times New Roman;width:100%;text-align:center;color:#555">Trang <span class="pageNumber"></span></div>'};
  let previous='';
  for(let pass=0;pass<4;pass++){
   await page.pdf(options);
   const output=execFileSync(process.env.PYTHON||'python',[path.join(root,'scripts/pdf_report_pages.py')],{encoding:'utf8'});
   const numbers=JSON.parse(output);
   await page.evaluate(numbers=>{for(const [id,number] of Object.entries(numbers)){const node=document.querySelector(`[data-id="${id}"]`);if(node)node.textContent=String(number);}},numbers);
   const current=JSON.stringify(numbers);if(current===previous){console.log('PDF rendered; measured TOC stabilized after '+(pass+1)+' passes.');break;}previous=current;
   if(pass===3)throw Error('PDF table of contents pagination did not stabilize');
  }
  fs.writeFileSync(path.join(folder,'pdf_render.json'),JSON.stringify({renderer:'local Chromium via Playwright',images:images.length,headings:headings.length,toc:'page numbers measured from rendered PDF',word_export:'not completed; DOCX preserved'},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
