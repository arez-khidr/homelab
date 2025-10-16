# If you are following along with my blog post, this script tears down the AD environment

#NOTE: I have included excessive comments intentionally for educational purposes
# I typically (or am trying to avoid) too many comments. However I add comments
# So that newer users could use my script while following a long with my blog post.


$domain = Get-ADDomain
$domainDN = $domain.DistinguishedName

# Remove group memberships first

$memberships = @(
    @{User="kurt.admin"; Group="IT-Administrators"},
    @{User="adam.helpdesk"; Group="IT-Administrators"},
    @{User="kurt.admin"; Group="Server-Admins"}
)

foreach ($m in $memberships) {
  try {
      Remove-ADGroupMember -Identity $m.Group -Members $m.User -Confirm:$false -ErrorAction Stop
  } catch {
      Write-Host "Error removing $($m.User) from $($m.Group)"
  }
}

# Remove the group policy objects

try {
  Remove-GPLink -Name "IT Security Policy" -Target "OU=IT-Department,$domainDN" -ErrorAction Stop
  Remove-GPO -Name "IT Security Policy" -ErrorAction Stop
} catch {
  Write-Host "Error removing GPO IT Security Policy"
}

try {
  Remove-GPLink -Name "Server Hardening Policy" -Target "OU=Servers,$domainDN" -ErrorAction Stop
  Remove-GPO -Name "Server Hardening Policy" -ErrorAction Stop
} catch {
  Write-Host "Error removing GPO Server Hardening Policy"
}

# Remove the groups

$groups = @(
  @{Name="IT-Administrators"; OU="OU=IT-Department,$domainDN"; Description="IT Admin Group"},
  @{Name="Server-Admins"; OU="OU=Servers,$domainDN"; Description="Server Administrators"}
)

foreach ($g in $groups) {
  try {
      Remove-ADGroup -Identity $g.Name -Confirm:$false -ErrorAction Stop
  } catch {
      Write-Host "Error removing group $($g.Name)"
  }
}

# Remove the computer objects

$computers = @(
  @{Name="WS-ADMIN-01"; OU="OU=IT-Department,$domainDN"; Description="Admin Workstation"},
  @{Name="SQL-SERVER-01"; OU="OU=Servers,$domainDN"; Description="SQL Database Server"},
  @{Name="WEB-SERVER-01"; OU="OU=Servers,$domainDN"; Description="Web Server"}
)

foreach ($c in $computers) {
  try {
      Remove-ADComputer -Identity $c.Name -Confirm:$false -ErrorAction Stop
  } catch {
      Write-Host "Error removing computer $($c.Name)"
  }
}

# Remove the users

$users = @(
  @{Name="kurt.admin"; DisplayName="Kurt Admin"; OU="OU=IT-Department,$domainDN"; Password="Summer2024!"},
  @{Name="adam.helpdesk"; DisplayName="Adam Helpdesk"; OU="OU=IT-Department,$domainDN"; Password="Password123!"}
)

foreach ($u in $users) {
  try {
      Remove-ADUser -Identity $u.Name -Confirm:$false -ErrorAction Stop
  } catch {
      Write-Host "Error removing user account $($u.Name)"
  }
}

# Remove the organizational Units

$OUNames = @("IT-Department", "Servers")

foreach ($name in $OUNames) {
  try {
      Remove-ADOrganizationalUnit -Identity "OU=$name,$domainDN" -Recursive -Confirm:$false -ErrorAction Stop
    } catch {
        Write-Host "Error removing $name"
      }
}



