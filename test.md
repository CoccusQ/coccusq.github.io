# 第六章 作业
## 6.2
### a. $\Pi_{person\_name}(\sigma_{city='Miami'}(employee))$
### b. $\Pi_{person\_name}(\sigma_{salary>100000}(works))$
### c. $\Pi_{person\_name}(\sigma_{city='Miami'\wedge salary>100000}(employee\times works))$
## 6.3
### a. $\Pi_{branch\_name}(\sigma_{branch\_city='Chicago'}(branch))$
### b. $\Pi_{ID}(\sigma_{branch\_name='Downtown'}(branch\times loan\times borrower))$
## 6.4
### a. $\Pi_{person\_name}(\sigma_{company\_name\ne'BigBank'}(works))$
### b. $\Pi_{person\_name}(\sigma_{salary\ge\{s\,|\,\forall\,s\,\in\,\Pi_{salary}(works)\}}(works))$
## 6.10
### a. $\Pi_{person\_name}(\sigma_{company\_name='BigBank'}(works))$
### b. $\Pi_{person\_name,\,city}(\sigma_{company\_name='BigBank'}(works\times employee))$
### c. $\Pi_{person\_name,\,street,\,city}(\sigma_{company\_name='BigBank'\wedge salary>100000}(works\times employee))$
### d. $\Pi_{person\_name}(\sigma_{employee.city=company.city}(employee\times works\times company))$