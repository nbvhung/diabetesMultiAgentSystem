import { describe, it, expect, vi, afterEach } from 'vitest';
import { citationUrl, validateAssessment, synthetic, request } from './api';
afterEach(()=>vi.unstubAllGlobals());
describe('assessment validation',()=>{
  const sample=Object.fromEntries(Object.entries(synthetic).map(([k,v])=>[k,String(v)]));
  it('accepts eight synthetic numeric features including zero',()=>expect(validateAssessment(sample)).toBe(''));
  it.each([['age','1.5'],['pregnancies','-1'],['glucose',''],['bmi','Infinity'],['age','0']])('rejects invalid %s %s',(key,value)=>expect(validateAssessment({...sample,[key]:value})).not.toBe(''));
});
describe('evidence links',()=>{
  it('accepts approved HTTPS source',()=>expect(citationUrl('https://www.niddk.nih.gov/health-information/diabetes/overview')).toMatch(/^https:/));
  it.each(['javascript:alert(1)','https://evil.example','https://www.niddk.nih.gov@evil.example/x','http://www.niddk.nih.gov/x','https://www.niddk.nih.gov/x?redirect=evil','https://www.niddk.nih.gov:8443/x'])('rejects %s',value=>expect(citationUrl(value)).toBeNull());
});
it('surfaces persistence failure without displaying server exception text',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:false,status:503,json:async()=>({detail:'SECRET'})}));
  await expect(request('/api/v1/mas/runs')).rejects.toThrow('Dependency chưa sẵn sàng');
});
