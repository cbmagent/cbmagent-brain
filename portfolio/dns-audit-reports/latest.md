# Read-Only Domain Audit

Generated UTC: `2026-05-03T21-34-18Z`

This audit used public DNS and HTTP(S) checks only. It did not mutate any provider state.

## Summary

- **aprilmoyer.com**: `no-apex-records-detected`; HTTPS `None` → `https://aprilmoyer.com/`
- **aprilunlimited.com**: `wordpress-detected`; HTTPS `200` → `https://aprilunlimited.com/`
- **clarkemoyer.com**: `github-pages-detected`; HTTPS `200` → `https://clarkemoyer.com/`
- **clarkmoyer.com**: `redirect-only-candidate`; HTTPS `200` → `https://clarkemoyer.com/`
- **completequarters.com**: `no-apex-records-detected`; HTTPS `None` → `https://completequarters.com/`
- **completequarters.org**: `redirect-only-candidate`; HTTPS `None` → `https://completequarters.org/`
- **darkclouds.us**: `no-apex-records-detected`; HTTPS `None` → `https://darkclouds.us/`
- **focus-on-free.com**: `wordpress-detected`; HTTPS `200` → `https://focus-on-free.com/`
- **focusonfree.org**: `dns-present-http-issue`; HTTPS `403` → `https://focusonfree.org/`
- **focusonfree.us**: `dns-present-http-issue`; HTTPS `403` → `https://focusonfree.us/`
- **moyermanagement.com**: `wordpress-detected`; HTTPS `200` → `https://moyermanagement.com/`
- **moyermanagement.org**: `redirect-only-candidate`; HTTPS `None` → `https://moyermanagement.org/`
- **moyermanagementsystems.com**: `no-apex-records-detected`; HTTPS `None` → `https://moyermanagementsystems.com/`
- **physicalinvestor.com**: `dns-present-http-issue`; HTTPS `403` → `https://physicalinvestor.com/`
- **technologyadoptionbarriers.org**: `github-pages-detected`; HTTPS `200` → `https://technologyadoptionbarriers.org/`

## Details

### aprilmoyer.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `no-apex-records-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `none`
- AAAA: `none`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://aprilmoyer.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`
- HTTP: `None` `http://aprilmoyer.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`

### aprilunlimited.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `wordpress-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `104.21.30.239, 172.67.174.48`
- AAAA: `2606:4700:3036::6815:1eef, 2606:4700:3036::ac43:ae30`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `200` `https://aprilunlimited.com/` ``
- HTTP: `200` `https://aprilunlimited.com/` ``

### clarkemoyer.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `cbmagent/clarkemoyer.com`
- Classification: `github-pages-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `185.199.111.153, 185.199.108.153, 185.199.110.153, 185.199.109.153`
- AAAA: `2606:50c0:8000::153, 2606:50c0:8003::153, 2606:50c0:8002::153, 2606:50c0:8001::153`
- CNAME apex: `none`
- www CNAME: `clarkemoyer.github.io`
- HTTPS: `200` `https://clarkemoyer.com/` ``
- HTTP: `200` `https://clarkemoyer.com/` ``

### clarkmoyer.com

- Role: `redirect-only`
- Target hosting: `cloudflare-redirect`
- Repo: `None`
- Classification: `redirect-only-candidate`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `172.67.143.213, 104.21.95.81`
- AAAA: `2606:4700:3034::6815:5f51, 2606:4700:3034::ac43:8fd5`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `200` `https://clarkemoyer.com/` ``
- HTTP: `200` `https://clarkemoyer.com/` ``

### completequarters.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `no-apex-records-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `none`
- AAAA: `none`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://completequarters.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`
- HTTP: `None` `http://completequarters.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`

### completequarters.org

- Role: `redirect-only`
- Target hosting: `cloudflare-redirect`
- Repo: `None`
- Classification: `redirect-only-candidate`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `none`
- AAAA: `none`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://completequarters.org/` `URLError: <urlopen error [Errno -2] Name or service not known>`
- HTTP: `None` `http://completequarters.org/` `URLError: <urlopen error [Errno -2] Name or service not known>`

### darkclouds.us

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `no-apex-records-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `none`
- AAAA: `none`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://darkclouds.us/` `URLError: <urlopen error [Errno -2] Name or service not known>`
- HTTP: `None` `http://darkclouds.us/` `URLError: <urlopen error [Errno -2] Name or service not known>`

### focus-on-free.com

- Role: `canonical-or-related-site`
- Target hosting: `github-pages-or-redirect`
- Repo: `TBD`
- Classification: `wordpress-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `104.21.87.115, 172.67.143.6`
- AAAA: `2606:4700:3030::6815:5773, 2606:4700:3032::ac43:8f06`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `200` `https://focus-on-free.com/` ``
- HTTP: `200` `https://focus-on-free.com/` ``

### focusonfree.org

- Role: `canonical-or-related-site`
- Target hosting: `github-pages-or-redirect`
- Repo: `TBD`
- Classification: `dns-present-http-issue`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `104.21.21.230, 172.67.200.242`
- AAAA: `2606:4700:3032::6815:15e6, 2606:4700:3034::ac43:c8f2`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `403` `https://focusonfree.org/` `HTTP Error 403: Forbidden`
- HTTP: `403` `http://focusonfree.org/` `HTTP Error 403: Forbidden`

### focusonfree.us

- Role: `canonical-or-related-site`
- Target hosting: `github-pages-or-redirect`
- Repo: `TBD`
- Classification: `dns-present-http-issue`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `172.67.176.160, 104.21.80.88`
- AAAA: `2606:4700:3033::ac43:b0a0, 2606:4700:3033::6815:5058`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `403` `https://focusonfree.us/` `HTTP Error 403: Forbidden`
- HTTP: `403` `http://focusonfree.us/` `HTTP Error 403: Forbidden`

### moyermanagement.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `wordpress-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `172.67.135.216, 104.21.26.99`
- AAAA: `2606:4700:3037::ac43:87d8, 2606:4700:3033::6815:1a63`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `200` `https://moyermanagement.com/` ``
- HTTP: `200` `https://moyermanagement.com/` ``

### moyermanagement.org

- Role: `redirect-only`
- Target hosting: `cloudflare-redirect`
- Repo: `None`
- Classification: `redirect-only-candidate`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `172.67.145.29, 104.21.63.94`
- AAAA: `2606:4700:3030::6815:3f5e, 2606:4700:3034::ac43:911d`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://moyermanagement.org/` `TimeoutError: The read operation timed out`
- HTTP: `None` `http://moyermanagement.org/` `TimeoutError: The read operation timed out`

### moyermanagementsystems.com

- Role: `canonical-or-related-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `no-apex-records-detected`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `none`
- AAAA: `none`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `None` `https://moyermanagementsystems.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`
- HTTP: `None` `http://moyermanagementsystems.com/` `URLError: <urlopen error [Errno -2] Name or service not known>`

### physicalinvestor.com

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `TBD`
- Classification: `dns-present-http-issue`
- NS: `cody.ns.cloudflare.com, lisa.ns.cloudflare.com`
- A: `172.67.172.185, 104.21.30.98`
- AAAA: `2606:4700:3033::ac43:acb9, 2606:4700:3032::6815:1e62`
- CNAME apex: `none`
- www CNAME: `none`
- HTTPS: `403` `https://physicalinvestor.com/` `HTTP Error 403: Forbidden`
- HTTP: `403` `http://physicalinvestor.com/` `HTTP Error 403: Forbidden`

### technologyadoptionbarriers.org

- Role: `canonical-site`
- Target hosting: `github-pages`
- Repo: `clarkemoyer/technologyadoptionbarriers.org`
- Classification: `github-pages-detected`
- NS: `ns1.freeforcharity.org, ns2.freeforcharity.org`
- A: `185.199.110.153, 185.199.111.153, 185.199.108.153, 185.199.109.153`
- AAAA: `2606:50c0:8001::153, 2606:50c0:8000::153, 2606:50c0:8002::153, 2606:50c0:8003::153`
- CNAME apex: `none`
- www CNAME: `clarkemoyer.github.io`
- HTTPS: `200` `https://technologyadoptionbarriers.org/` ``
- HTTP: `200` `https://technologyadoptionbarriers.org/` ``

