from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .helpers.get_data_by_inn import get_data
from .models import Calculation, ParameterGroup, Parameter, ParameterOption, CalculationParameterData, CalculationResult
from django.db.models import Q, Prefetch, F, Sum, Max
from django.db import transaction
from django.http import JsonResponse
from datetime import datetime
from collections import defaultdict
import json

# Create your views here.
@login_required(login_url="/users/login/")
def newcalc_view(requset):
    return render(requset, "calculations/newcalc.html")


@login_required(login_url="/users/login/")
def company_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'fetch':
            inn = request.POST.get('inn', '').strip()
            if not inn:
                messages.error(request, "Поле ИНН обязательно для запроса.")
                return render(request, 'calculations/newcalc.html')
            data = get_data(inn)
            if isinstance(data, dict):
                data["inn"] = inn
                return render(request, 'calculations/newcalc.html', {'data': data})
            else:
                messages.error(request, data)
                return render(request, 'calculations/newcalc.html', {'data' : {"inn":inn}})

        elif action == 'calculate':
            required_fields = ['inn', 'name', 'kpp', 'ogrn', 'address']
            data = { i : request.POST.get(i, '').strip() for i in required_fields }
            if '' in data.values():
                messages.error(request, "Заполните все поля перед расчетом.")
                return render(request, 'calculations/newcalc.html', {'data': data})
            
            if (len(data["inn"]) != 12 and len(data["inn"]) != 10) or not all(i.isdigit() for i in data["inn"]):
                messages.error(request, "Некорректный формат ИНН.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            if len(data["kpp"]) != 9 or not all(i.isdigit() for i in data["kpp"]):
                messages.error(request, "Некорректный формат КПП.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            if len(data["ogrn"]) != 13 or not all(i.isdigit() for i in data["ogrn"]):
                messages.error(request, "Некорректный формат ОГРН.")
                return render(request, 'calculations/newcalc.html', {'data': data})

            new_calculation = Calculation(
                user = request.user,
                organisation_INN = data["inn"],
                organisation_KPP = data["kpp"],
                organisation_OGRN = data["ogrn"],
                organisation_name = data["name"],
                organisation_address = data["address"],
            )
            new_calculation.save()
            
            return redirect('calculations:rX', calc_id=new_calculation.id, group_code='r0')

    return render(request, 'calculations/newcalc.html')


@login_required(login_url="/users/login/")
def fill_by_inn(request, inn):
    try:
        calc = Calculation.objects.filter(organisation_INN=inn).latest("created")
        data = {
            "found": True,
            "inn": calc.organisation_INN,
            "kpp": calc.organisation_KPP,
            "ogrn": calc.organisation_OGRN,
            "name": calc.organisation_name,
            "address": calc.organisation_address,
        }
    except Calculation.DoesNotExist:
        data = {"found": False}
    return JsonResponse(data)

PARAMETER_CODES = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8']

@login_required(login_url="/users/login/")
def rX_view(request, calc_id, group_code):
    calculation = get_object_or_404(Calculation, id=calc_id, user=request.user)
    if (calculation.is_complete):
        return redirect('calculations:history')
    group = get_object_or_404(ParameterGroup, code=group_code)

    if group_code == 'r0':
        all_parameters = Parameter.objects.all()
        for p in all_parameters:
            CalculationParameterData.objects.get_or_create(
                calculation=calculation,
                parameter=p,
                defaults={
                    "value_before": "",
                    "actions_description": ""
                }
            )

    parameters = Parameter.objects.filter(group=group).order_by('order_num')

    param_data_dict = {
        pd.parameter_id: pd
        for pd in CalculationParameterData.objects.filter(
            calculation=calculation,
            parameter__in=parameters
        )
    }

    parent_param_data_dict = {}
    if calculation.parent:
        parent_param_data_dict = {
            pd.parameter_id: pd
            for pd in CalculationParameterData.objects.filter(
                calculation=calculation.parent,
                parameter__in=parameters
            )
        }

    for p in parameters:
        p.data = param_data_dict.get(p.id)
        p.parent_data = parent_param_data_dict.get(p.id)
    
    next_code = None
    current_index = PARAMETER_CODES.index(group_code)
    prev_code = PARAMETER_CODES[current_index - 1] if current_index > 0 else None

    if request.method == "POST":
        for param in parameters:
            value_before = request.POST.get(f"before_{param.id}", "")
            actions_description = request.POST.get(f"actions_{param.id}", "")

            CalculationParameterData.objects.filter(
                calculation=calculation,
                parameter=param
            ).update(
                value_before=value_before,
                actions_description=actions_description
            )

        current_index = PARAMETER_CODES.index(group_code)
        if current_index < len(PARAMETER_CODES) - 1:
            next_code = PARAMETER_CODES[current_index + 1]
            return redirect('calculations:rX', calc_id=calculation.id, group_code=next_code)
        else:
            if request.POST.get("confirm_finish") == "1":
                calculation.is_complete = True
                calculation.save()
                return redirect('calculations:history')

    context = {
        "calculation": calculation,
        "group": group,
        "parameters": parameters,
        "next_code": next_code,
        "prev_code": prev_code,
    }

    return render(request, "calculations/rX.html", context)


@login_required(login_url="/users/login/")
def history_view(request):
    user = request.user
    sort_param = request.GET.get("sort", "-created")
    filter_by = request.GET.get("filter_by", "")
    query = request.GET.get("query", "").strip()
    created_from = request.GET.get("created_from")
    created_to = request.GET.get("created_to")

    qs = Calculation.objects.all() if user.groups.filter(name="boss").exists() else Calculation.objects.filter(user=user)

    if filter_by and query:
        if filter_by == "organisation_INN":
            qs = qs.filter(organisation_INN__icontains=query)
        elif filter_by == "organisation_name":
            qs = qs.filter(organisation_name__icontains=query)
        elif filter_by == "user":
            qs = qs.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query)
            )

    if created_from:
        try:
            created_from_date = datetime.strptime(created_from, "%Y-%m-%d")
            qs = qs.filter(created__date__gte=created_from_date)
        except ValueError:
            pass
    if created_to:
        try:
            created_to_date = datetime.strptime(created_to, "%Y-%m-%d")
            qs = qs.filter(created__date__lte=created_to_date)
        except ValueError:
            pass

    allowed_sort_fields = {
        "user", "-user", "created", "-created",
        "organisation_INN", "-organisation_INN",
        "organisation_name", "-organisation_name",
        "is_complete", "-is_complete"
    }
    if sort_param not in allowed_sort_fields:
        sort_param = "-created"

    qs = qs.order_by(sort_param)

    headers = {
        "user": "Пользователь",
        "created": "Дата создания",
        "organisation_INN": "ИНН",
        "organisation_name": "Наименование",
        "is_complete": "Статус",
    }

    return render(request, "calculations/history.html", {
        "calculations": qs,
        "headers": headers,
        "current_sort": sort_param,
    })


@login_required(login_url="/users/login/")
def save_param_value(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"})

    try:
        data = json.loads(request.body)
        calc_id = data.get("calc_id")
        param_id = data.get("param_id")
        field_type = data.get("field_type")
        value = data.get("value")

        try:
            calc = Calculation.objects.get(id=calc_id, user=request.user)
        except Calculation.DoesNotExist:
            return JsonResponse({"success": False, "error": "Calculation not found or access denied"})

        if field_type not in ["value_before", "value_after", "actions_description"]:
            return JsonResponse({"success": False, "error": "Invalid field type"})

        cp_data, created = CalculationParameterData.objects.get_or_create(
            calculation_id=calc_id,
            parameter_id=param_id,
            defaults={"value_before": "", "value_after": "", "actions_description": ""}
        )

        setattr(cp_data, field_type, value)
        cp_data.save()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def get_linguistic_level(percentage):
    if percentage < 10:
        return 'Низкий уровень опасности'
    elif percentage < 20:
        return 'Умеренный уровень опасности'
    elif percentage < 33:
        return 'Средний уровень опасности'
    elif percentage < 50:
        return 'Значительный уровень опасности'
    elif percentage < 90:
        return 'Высокий уровень опасности'
    else:
        return 'Чрезвычайно высокий уровень опасности'


recomendations = {
    'Не оценивается' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности",
    'Низкий уровень опасности' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности",
    'Умеренный уровень опасности' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности",
    'Средний уровень опасности' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности. Разработка плана выполнения мероприятий по снижению категории опасности (риска) аварии",
    'Значительный уровень опасности' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности. Разработка плана выполнения мероприятий по снижению категории опасности (риска) аварии",
    'Высокий уровень опасности' : "Поддержание системы противоаварийной защиты в работоспособном состоянии; контроль источников опасности; контроль возникновения новых источников опасности. Разработка плана выполнения мероприятий по снижению категории опасности (риска) аварии. Главному инженеру необходимо разработать и утвердить обоснование возможности безопасного ведения работ, обеспечиваемой за счет снижения нагрузки и принятия дополнительных защитных мероприятий до снижения категории опасности (риска) аварии",
    'Чрезвычайно высокий уровень опасности' : "Обязательная приостановка горных работ, кроме работ по поддержанию жизнедеятельности шахты - проветривание, откачка воды и устранения причин недопустимого уровня риска аварии до снижения категории опасности (риска) аварии до допустимого уровня"
}


def get_conclusion(before_percentage, after_percentage, group_code):
    if before_percentage == 0.0 and group_code in ['r1', 'r2', 'r3', 'r4', 'r5', 'r8']:
        return 'Не оценивается'
    elif before_percentage == after_percentage:
        return 'Уровень риска без изменений'
    elif after_percentage < before_percentage:
        return 'Уровень риска уменьшился, уровень безопасности увеличился'
    else:
        return 'Уровень риска увеличился, уровень безопасности снизился'


@login_required(login_url="/users/login/")
def calc_details_view(request, pk):
    calculation = get_object_or_404(Calculation, pk=pk)
    if request.user != calculation.user and not user.groups.filter(name="boss").exists():
        return redirect('calculations:history')

    if not calculation.is_complete:
        return redirect('calculations:rX', calc_id=calculation.id, group_code='r0')

    results = CalculationResult.objects.filter(calculation=calculation).order_by('group__code')

    if not results.exists():
        parameter_groups = ParameterGroup.objects.all().order_by('code')
        
        total_before_sum = 0
        total_max_sum = 0
        
        max_group_before_percentage = 0
        
        r0_results = None

        for group in parameter_groups:
            difference = 0
            conclusion = "Не оценивается"
            group_data = CalculationParameterData.objects.filter(
                calculation=calculation,
                parameter__group=group
            ).select_related('parameter', 'parameter__group')

            first_param_coefficient = -1
            if group.code in ['r1', 'r2', 'r3', 'r5', 'r8']:
                first_param_data = group_data.filter(parameter__order_num=1).first()
                if first_param_data:
                    try:
                        first_param_option = ParameterOption.objects.get(
                            parameter=first_param_data.parameter,
                            text=first_param_data.value_before
                        )
                        first_param_coefficient = first_param_option.coefficient
                    except ParameterOption.DoesNotExist:
                        pass

            r4_coefficients_zero = False
            if group.code == 'r4':
                r4_data = group_data.filter(parameter__order_num__lte=4)
                r4_coefficients = []
                for data in r4_data:
                    try:
                        option = ParameterOption.objects.get(
                            parameter=data.parameter,
                            text=data.value_before
                        )
                        r4_coefficients.append(option.coefficient)
                    except ParameterOption.DoesNotExist:
                        pass
                if len(r4_coefficients) == 4 and all(c == 0 for c in r4_coefficients):
                    r4_coefficients_zero = True

            group_before_sum = 0
            group_max_sum = 0

            if (group.code in ['r1', 'r2', 'r3', 'r5', 'r8'] and first_param_coefficient == 0) or r4_coefficients_zero:
                before_percentage = 0.0
                after_percentage = 0.0
                before_linguistic_level = 'Не оценивается'
            else:
                for data in group_data:
                    try:
                        option_before = ParameterOption.objects.get(parameter=data.parameter, text=data.value_before)
                        group_before_sum += option_before.coefficient
                    except ParameterOption.DoesNotExist:
                        pass

                group_max_sum_list = [
                    ParameterOption.objects.filter(parameter=p.parameter).aggregate(max_coeff=Max('coefficient'))['max_coeff'] or 0
                    for p in group_data
                ]
                group_max_sum = sum(group_max_sum_list)

                r0_before_sum = 0 if r0_results is None else r0_results.before_sum
                r0_max_sum = 0 if r0_results is None else r0_results.max_sum
                before_percentage = ((group_before_sum + r0_before_sum) / (group_max_sum + r0_max_sum)) * 100 if group_max_sum > 0 else 0.0
                before_linguistic_level = get_linguistic_level(before_percentage)
                
                if calculation.parent:
                    difference = before_percentage - CalculationResult.objects.get(calculation=calculation.parent, group=group).before_percentage
                    conclusion = get_conclusion(CalculationResult.objects.get(calculation=calculation.parent, group=group).before_percentage, before_percentage, group.code)

            total_before_sum += group_before_sum
            total_max_sum += group_max_sum

            if before_percentage > max_group_before_percentage:
                max_group_before_percentage = before_percentage
            

            res = CalculationResult.objects.create(
                calculation=calculation,
                group=group,
                before_sum=group_before_sum,
                before_percentage=before_percentage,
                before_linguistic_level=before_linguistic_level,
                max_sum=group_max_sum,
                difference = difference,
                conclusion = conclusion,
            )

            if group.code == 'r0':
                r0_results = res

        results = CalculationResult.objects.filter(calculation=calculation).order_by('group__code')

    total_max_sum = sum(r.max_sum for r in results)
    total_before_sum = sum(r.before_sum for r in results)
    total_before_percentage = (total_before_sum / total_max_sum) * 100 if total_max_sum > 0 else 0.0
    max_group_before_percentage = max(r.before_percentage for r in results)

    total_after_sum = 0
    total_after_percentage = 0
    max_group_after_percentage = 0
    after_results = []
    if calculation.parent:
        after_results = CalculationResult.objects.filter(calculation=calculation.parent).order_by('group__code')
        total_after_sum = sum(r.before_sum for r in after_results)
        total_after_percentage = (total_after_sum / total_max_sum) * 100 if total_max_sum > 0 else 0.0
        max_group_after_percentage = max(r.before_percentage for r in after_results)

    user = request.user
    qs = Calculation.objects.filter(parent=calculation)() if user.groups.filter(name="boss").exists() else Calculation.objects.filter(user=user, parent=calculation)
    headers = {
        "user": "Пользователь",
        "created": "Дата создания",
        "organisation_INN": "ИНН",
        "organisation_name": "Наименование",
        "is_complete": "Статус",
    }
        
    context = {
        'calculation': calculation,
        'results': results,
        'after_results': after_results,
        'total_before_percentage': total_before_percentage,
        'total_after_percentage': total_after_percentage,
        'total_before_linguistic_level': get_linguistic_level(total_before_percentage),
        'total_after_linguistic_level': get_linguistic_level(total_after_percentage),
        'total_difference': total_before_percentage - total_after_percentage,
        'total_conclusion': get_conclusion(total_after_percentage, total_before_percentage, 'R'),
        'max_before_percentage': max_group_before_percentage,
        'max_after_percentage': max_group_after_percentage,
        'max_before_linguistic_level': get_linguistic_level(max_group_before_percentage),
        'max_after_linguistic_level': get_linguistic_level(max_group_after_percentage),
        'max_difference': max_group_before_percentage - max_group_after_percentage,
        'max_conclusion': get_conclusion(max_group_after_percentage, max_group_before_percentage, 'R'),
        'recomendations_before': recomendations[get_linguistic_level(max_group_before_percentage)],
        'recomendations_after': recomendations[get_linguistic_level(max_group_after_percentage)],
        "calculations": qs,
        "headers": headers,
    }

    if request.method == "POST":
        if request.POST.get("confirm_finish") == "1":
            calculation.delete()
            return redirect('calculations:history')

    return render(request, 'calculations/calc_details.html', context)


@login_required(login_url="/users/login/")
def calc_answers_view(request, pk):
    calculation_meta = get_object_or_404(
        Calculation.objects.only('user_id', 'is_complete'),
        pk=pk
    )

    if (request.user != calculation_meta.user and not request.user.groups.filter(name="boss").exists()) or not calculation_meta.is_complete:
        return redirect('calculations:history')

    calculation = (
        Calculation.objects
        .prefetch_related(
            Prefetch(
                'parameter_data',
                queryset=CalculationParameterData.objects
                    .select_related('parameter', 'parameter__group')
                    .order_by('parameter__order_num')
            )
        )
        .get(pk=pk)
    )

    groups = list(ParameterGroup.objects.filter(code__in=PARAMETER_CODES).order_by('code'))

    grouped_data = defaultdict(list)
    for pdata in calculation.parameter_data.all():
        grouped_data[pdata.parameter.group_id].append(pdata)

    groups_with_data = [
        (group, grouped_data.get(group.id, []))
        for group in groups
    ]

    return render(request, 'calculations/calc_answers.html', {
        'calculation': calculation,
        'groups_with_data': groups_with_data
    })



@login_required(login_url="/users/login/")
def create_related_calculation(request, pk):
    calc = get_object_or_404(Calculation, pk=pk, user=request.user)

    if request.method == "POST":
        new_calc = Calculation.objects.create(
            user=request.user,
            parent=calc,
            organisation_INN=calc.organisation_INN,
            organisation_KPP=calc.organisation_KPP,
            organisation_OGRN=calc.organisation_OGRN,
            organisation_name=calc.organisation_name,
            organisation_address=calc.organisation_address,
        )

        for param_data in CalculationParameterData.objects.filter(calculation=calc):
            CalculationParameterData.objects.create(
                calculation=new_calc,
                parameter=param_data.parameter,
                value_before=param_data.value_before,
                actions_description=""
            )

        return redirect("calculations:calc_details", pk=new_calc.pk)

    return redirect("calculations:calc_details", pk=pk)
