# If you are following along with my blog post, ensure that you have already configured a domain 

#NOTE: I have included excessive comments intentionally for educational purposes  
# I typically (or am trying to avoid) too many comments. However I add comments 
# So that newer users could use my script while following a long with my blog post.


$domain = Get-ADDomain 
$domainDN = $domain.DistinguishedName

# Generate the organizational Units 

$OUNames = @("IT-Department", "Servers") 

foreach ($name in $OUNames) {
  try {
      New-ADOrganizationalUNit -Name $name -Path $domainDN
    } catch {
        Write-Host "Error generating $name"
      }
}

# Generate the users 

$users = @(
  @{Name="kurt.admin"; DisplayName="Kurt Admin"; OU="OU=IT-Department,$domainDN"; Password="Summer2024!"},
  @{Name="adam.helpdesk"; DisplayName="Adam Helpdesk"; OU="OU=IT-Department,$domainDN"; Password="Password123!"}
)

foreach ($u in $users) {
  try {
      New-ADUser -Name $u.Name `
                  -DisplayName $u.DisplayName `
                  -SamAccountName $u.Name `
                  -UserPrincipalName "$($u.Name)@$($domain.DNSRoot)" `
                  -Path $u.OU `
                  -AccountPassword (ConvertTo-SecureString $u.Password -AsPlainText -Force) `
                  -Enabled $true `
                  -PasswordNeverExpires $true `
                  -ErrorAction Stop
  } catch {
      Write-Host "Error generating user account $u.Name"
  }
}

# Genereate the computer objects  

$computers = @(
  @{Name="WS-ADMIN-01"; OU="OU=IT-Department,$domainDN"; Description="Admin Workstation"},
  @{Name="SQL-SERVER-01"; OU="OU=Servers,$domainDN"; Description="SQL Database Server"},
  @{Name="WEB-SERVER-01"; OU="OU=Servers,$domainDN"; Description="Web Server"}
)

foreach ($c in $computers) {
  try {
      New-ADComputer -Name $c.Name `
                      -Path $c.OU `
                      -Description $c.Description `
                      -Enabled $true `
                      -ErrorAction Stop
  } catch {
      Write-Host "Error generating computer $c.Name" 
  }
}

#Generate the group 

$groups = @(
  @{Name="IT-Administrators"; OU="OU=IT-Department,$domainDN"; Description="IT Admin Group"},
  @{Name="Server-Admins"; OU="OU=Servers,$domainDN"; Description="Server Administrators"}
)

foreach ($g in $groups) {
  try {
      New-ADGroup -Name $g.Name `
                  -Path $g.OU `
                  -GroupScope Global `
                  -GroupCategory Security `
                  -Description $g.Description `
                  -ErrorAction Stop
  } catch {
      Write-Host "Error creating group $g.Name" 
  }
}

$memberships = @(
    @{User="kurt.admin"; Group="IT-Administrators"},
    @{User="adam.helpdesk"; Group="IT-Administrators"},
    @{User="kurt.admin"; Group="Server-Admins"}
)

foreach ($m in $memberships) {
  try {
      Add-ADGroupMember -Identity $m.Group -Members $m.User -ErrorAction Stop
  } catch {
      Write-Host "Error adding $m.User to $m.Group" 
  }
}

#GEnereate group policy objects 

try {
  $gpo1 = New-GPO -Name "IT Security Policy" -Comment "Security settings for IT Department" -ErrorAction Stop
  New-GPLink -Name "IT Security Policy" -Target "OU=IT-Department,$domainDN" -LinkEnabled Yes -ErrorAction Stop
} catch {
  Write-Host "Error creating GPO IT Security Policy"
}

try {
  $gpo2 = New-GPO -Name "Server Hardening Policy" -Comment "Hardening settings for servers" -ErrorAction Stop
  New-GPLink -Name "Server Hardening Policy" -Target "OU=Servers,$domainDN" -LinkEnabled Yes -ErrorAction Stop
} catch {
  Write-Host "Error creating GPO Server Hardening Policy"
}




