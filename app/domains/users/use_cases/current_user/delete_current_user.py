from typing import Annotated

from fastapi import Depends

from app.domains.shared.transaction_managers import TransactionManagerDep


class DeleteUCurrentUserUseCase:
    def __init__(self, transaction_manager: TransactionManagerDep):
        self._tm = transaction_manager

    async def execute(self, current_user) -> None:
        async with self._tm:
            await self._tm.user_repository.mark_as_deleted(row_id=current_user.id)


DeleteCurrentUserUseCaseDep = Annotated[DeleteUCurrentUserUseCase, Depends()]
