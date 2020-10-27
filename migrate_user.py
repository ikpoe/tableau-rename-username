# Migrate user from username only to username@domain.com
# Limitation on the tableau API:
# Cannot migrate users with role:
# - ServerAdministator
# - SiteAdministratorCreator
# - Creator
# Cannot Set:
# - Display Name

import tableauserverclient as TSC

def main():
  tableau_auth = TSC.TableauAuth('USERNAME', 'PASSWORD')
  server = TSC.Server('http://tableau-url.com')
  original_user = "username"
  postfix = "@domain.com"

  with server.auth.sign_in(tableau_auth):
    migrate_user(server, original_user, postfix)

def migrate_user(server, username, postfix="@go-jek.com" ):
  old_user = get_user_by_name(server, username)
  new_user = replicate_user(server, old_user, postfix)
  transfer_workbook_owner(server, old_user, new_user)
  old_user = unlicense_by_username(server, username)
  return new_user

def replicate_user(server, old_user_item, postfix=None):
  if old_user_item.site_role == 'ServerAdministator':
    raise ValueError(f"Cannot Replicate user with Role {old_user_item.site_role}")

  new_name = add_postfix(old_user_item.name, postfix)
  replicated_user_item = TSC.UserItem(
    new_name, 
    old_user_item.site_role, 
    auth_setting=None,
    )
  replicated_user_item.email = old_user_item.email
  replicated_user_item.fullname = old_user_item.fullname

  new_user_item = server.users.add(replicated_user_item)

  new_user_item.name = new_user_item.name
  new_user_item.email = new_name
  new_user_item.fullname = old_user_item.fullname

  return server.users.update(new_user_item)
  
def add_postfix(username, postfix):
  if postfix in username:
    raise ValueError(f"The username {username} already contains postfix {postfix}")
  return username + postfix

def get_user_by_name(server, username):
  req_option = TSC.RequestOptions()
  req_option.filter.add(TSC.Filter(TSC.RequestOptions.Field.Name,
                                 TSC.RequestOptions.Operator.Equals,
                                 username))
  new_user_item, pagination_item = server.users.get(req_option)
  if not new_user_item:
    raise ValueError(f"Cannot find username {username} in {server.server_address}")
  return new_user_item[0]

def transfer_workbook_owner(server, src_user_item, dst_user_item):
  list_workbook = get_workbook_by_user(server, src_user_item)
  list_new_workbook = []
  for workbook in list_workbook:
    list_new_workbook.append(
      change_workbook_owner(server, workbook, dst_user_item)
    )
  return list_new_workbook

def get_workbook_by_user(server, user_item):
  # @TOFIX = Cannot retrieve workbooks owned by unlicensed users
  server.users.populate_workbooks(user_item)
  return [workbook for workbook in user_item.workbooks if workbook.owner_id == user_item.id]

def change_workbook_owner(server, workbook, user_item):
  workbook.owner_id = user_item.id
  return server.workbooks.update(workbook)

def unlicense_by_username(server, username):
  user_item = get_user_by_name(server, username)
  user_item.site_role = 'Unlicensed'
  return server.users.update(user_item)

if __name__ == '__main__':
    main()
